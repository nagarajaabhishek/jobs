"""Minimal stubs so Pyright resolves `import pytest` without the runtime package in the type-check venv."""

from typing import Any, Callable, ContextManager, NoReturn, TypeVar, overload

_F = TypeVar("_F", bound=Callable[..., Any])

def skip(reason: str = "", *, allow_module_level: bool = False) -> NoReturn: ...

@overload
def fixture(__func: _F) -> _F: ...
@overload
def fixture(*, scope: str = "function", autouse: bool = False, **kwargs: Any) -> Callable[[_F], _F]: ...
def fixture(__func: Any = None, **kwargs: Any) -> Any: ...

def raises(
    expected_exception: type[BaseException] | tuple[type[BaseException], ...],
    *,
    match: str | None = None,
) -> ContextManager[Any]: ...

class _Mark:
    def skipif(self, *args: Any, **kwargs: Any) -> Any: ...

mark: _Mark

def main(args: list[str] | None = None, plugins: Any = None) -> int | str: ...
