"""Failures are classified, retried once when temporary, logged with their cost, and explained to teachers."""
import datetime

import pytest
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from app import pipeline
from app.agents.planner import planner
from app.db import add_run, init_db, one, rows
from app.errors import AUTH, BUDGET, BUSY, INVALID_OUTPUT, TIMEOUT, TOO_LONG, UNKNOWN, classify, teacher_message


@pytest.mark.parametrize('error, expected', [
    (RuntimeError("You've used today's limit. It resets at midnight."), BUDGET),
    (UsageLimitExceeded('Exceeded the total_tokens_limit'), TOO_LONG),
    (ModelHTTPError(401, 'gpt-6-luna'), AUTH),
    (ModelHTTPError(403, 'gpt-6-luna'), AUTH),
    (ModelHTTPError(503, 'gpt-6-luna'), BUSY),
    (ModelHTTPError(429, 'gpt-6-luna'), BUSY),
    (ModelHTTPError(504, 'gpt-6-luna'), TIMEOUT),
    (UnexpectedModelBehavior('Exceeded maximum retries (2) for output validation'), INVALID_OUTPUT),
    (TimeoutError(), TIMEOUT),
    (ValueError('something else'), UNKNOWN),
])
def test_errors_are_classified(error, expected):
    assert classify(error) == expected


def test_only_auth_errors_mention_the_api_key():
    for error_type in (BUDGET, TOO_LONG, BUSY, TIMEOUT, INVALID_OUTPUT, UNKNOWN):
        assert 'API key' not in teacher_message(error_type)
    assert 'API key' in teacher_message(AUTH)


def _flaky_agent(failures, error):
    """An agent whose model fails `failures` times before answering."""
    calls = {'count': 0}

    def respond(messages, info):
        calls['count'] += 1
        if calls['count'] <= failures:
            raise error
        return ModelResponse(parts=[TextPart('ok')])
    return Agent(FunctionModel(respond), output_type=str), calls


def test_transient_failure_is_retried_once_and_logged():
    init_db()
    run_id = add_run('3A-TS')
    agent, calls = _flaky_agent(1, ModelHTTPError(503, 'gpt-6-luna'))
    result, _usage = pipeline._run(agent, 'hello', run_id, 'test_agent')
    assert result.output == 'ok'
    assert calls['count'] == 2
    agents = [row['agent_name'] for row in rows('select agent_name from llm_calls where run_id=?', (run_id,))]
    assert sorted(agents) == ['test_agent', 'test_agent_failed']


def test_auth_failure_is_not_retried():
    init_db()
    run_id = add_run('3A-TS')
    agent, calls = _flaky_agent(5, ModelHTTPError(401, 'gpt-6-luna'))
    with pytest.raises(ModelHTTPError):
        pipeline._run(agent, 'hello', run_id, 'test_agent')
    assert calls['count'] == 1


def test_failed_plan_saves_the_reason_and_shows_a_specific_message():
    init_db()

    def always_busy(messages, info):
        raise ModelHTTPError(503, 'gpt-6-luna')
    with planner.override(model=FunctionModel(always_busy)):
        result = pipeline.generate_plan('3A-TS', 'Mathematics', 'place value', lesson_type='5E', differentiated=True, differentiation_types=['product'])
    assert result['error_type'] == BUSY
    assert 'API key' not in result['error']
    run = one('select status, error_type, error_message from runs where id=?', (result['run_id'],))
    assert run['status'] == 'failed'
    assert run['error_type'] == BUSY
    assert 'ModelHTTPError' in run['error_message']


def test_invalid_plan_output_gets_the_invalid_output_message():
    init_db()

    def never_valid(messages, info):
        return ModelResponse(parts=[TextPart('not a lesson plan')])
    with planner.override(model=FunctionModel(never_valid)):
        result = pipeline.generate_plan('3A-TS', 'Mathematics', 'place value', lesson_type='5E')
    assert result['error_type'] == INVALID_OUTPUT
    assert one('select error_type from runs where id=?', (result['run_id'],))['error_type'] == INVALID_OUTPUT


def test_budget_uses_the_utc_date_the_timestamps_are_stored_in():
    assert pipeline.utc_today() == datetime.datetime.now(datetime.timezone.utc).date().isoformat()
