"""工具基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """工具抽象基类

    所有工具必须继承此类并实现:
    - name: 工具名称
    - description: 工具描述
    - execute: 执行逻辑
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义（OpenAI Function Calling 格式）"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具逻辑

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass
