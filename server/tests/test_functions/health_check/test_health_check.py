from app.utils.health_check import health_check_db


class TestFunctionHealthCheck:
    async def test_health_check_db(
        self,
        session
    ):
        health = await health_check_db(session)
        assert health
