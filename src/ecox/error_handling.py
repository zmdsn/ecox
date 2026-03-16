"""错误处理工具"""

from __future__ import annotations
import functools
import logging
from typing import Callable, Any, TypeAlias
from ecox.exceptions import EcoxException

logger = logging.getLogger(__name__)

AnyCallable: TypeAlias = Callable[..., Any]


def handle_errors(
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "ERROR"
) -> Callable[[AnyCallable], AnyCallable]:
    """
    错误处理装饰器

    Args:
        default_return: 发生错误时的默认返回值
        raise_on_error: 是否重新抛出异常
        log_level: 日志级别
    """
    def decorator(func: AnyCallable) -> AnyCallable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except EcoxException as e:
                # 已知业务异常
                getattr(logger, log_level.lower())(
                    f"{func.__name__} failed: {e.message}",
                    extra={"details": e.details}
                )
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                # 未知异常
                logger.error(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if raise_on_error:
                    raise
                return default_return
        return wrapper
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable[[AnyCallable], AnyCallable]:
    """
    重试装饰器（用于外部数据源调用）

    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: AnyCallable) -> AnyCallable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

                    wait_time = delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)

        return wrapper
    return decorator
