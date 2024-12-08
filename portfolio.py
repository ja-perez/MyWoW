class Granularity:
    ONE_MINUTE = 'ONE_MINUTE'
    FIVE_MINUTES = 'FIVE_MINUTES'
    FIFTEEN_MINUTES = 'FIFTEEN_MINUTES'
    THIRTY_MINUTES = 'THIRTY_MINUTES'
    ONE_HOU = 'ONE_HOUR'
    TWO_HOUR = 'TWO_HOUR'
    SIX_HOUR = 'SIX_HOUR'
    ONE_DAY = 'ONE_DAY'

    @staticmethod
    def verify(granularity: str) -> bool:
        return granularity in [Granularity.ONE_MINUTE, Granularity.FIVE_MINUTES, Granularity.FIFTEEN_MINUTES,
                              Granularity.THIRTY_MINUTES, Granularity.ONE_HOU, Granularity.TWO_HOUR, Granularity.SIX_HOUR,
                              Granularity.ONE_DAY]