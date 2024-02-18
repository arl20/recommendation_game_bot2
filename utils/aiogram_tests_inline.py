from typing import Callable, Dict, Iterable, Union

from aiogram import Router, types
from aiogram.filters import Filter
from aiogram.fsm.state import State

from aiogram_tests.handler import TelegramEventObserverHandler


class InlineQueryHandler(TelegramEventObserverHandler):
    def __init__(
        self,
        callback: Callable,
        *filters: Filter,
        state: Union[State, str, None] = None,
        state_data: Dict = None,
        dp_middlewares: Iterable = None,
        exclude_observer_methods: Iterable = None,
        **kwargs,
    ):
        super().__init__(
            callback,
            *filters,
            state=state,
            state_data=state_data,
            dp_middlewares=dp_middlewares,
            exclude_observer_methods=exclude_observer_methods,
            **kwargs,
        )

    def register_handler(self) -> None:
        router = Router()
        self.dp.include_routers(router)
        router.inline_query.register(self._callback, *self._filters)

    async def feed_update(self, inline_query: types.InlineQuery, *args, **kwargs) -> None:
        await self.dp.feed_update(self.bot, types.Update(update_id=12345678, inline_query=inline_query))


class ChosenInlineHandler(TelegramEventObserverHandler):
    def __init__(
        self,
        callback: Callable,
        *filters: Filter,
        state: Union[State, str, None] = None,
        state_data: Dict = None,
        dp_middlewares: Iterable = None,
        exclude_observer_methods: Iterable = None,
        **kwargs,
    ):
        super().__init__(
            callback,
            *filters,
            state=state,
            state_data=state_data,
            dp_middlewares=dp_middlewares,
            exclude_observer_methods=exclude_observer_methods,
            **kwargs,
        )

    def register_handler(self) -> None:
        router = Router()
        self.dp.include_routers(router)
        router.chosen_inline_result.register(self._callback, *self._filters)

    async def feed_update(self, chosen_result: types.ChosenInlineResult, *args, **kwargs) -> None:
        await self.dp.feed_update(self.bot, types.Update(update_id=12345678, chosen_inline_result=chosen_result))
