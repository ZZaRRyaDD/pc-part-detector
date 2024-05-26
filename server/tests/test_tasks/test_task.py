import asyncio

from app.tasks import task_worker


class TestCeleryWorkers:
    async def test_call_func(self):
        number = 5
        expected = f"test task work {number}"
        assert expected == task_worker(number)

    async def test_base_scenario(self):
        number = 5
        expected = f"test task work {number}"
        result = task_worker.delay(number)
        assert expected == result.get()
    
    async def test_apply_async(self):
        number = 5
        expected = f"test task work {number}"
        countdown = 5
        result = task_worker.apply_async((number,), countdown=countdown)
        await asyncio.sleep(countdown)
        assert expected == result.get()
