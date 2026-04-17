"""
Configuration Schema Definitions

Pydantic v2 models for configuration validation with type constraints,
range validation, and enum support.
"""

from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic import RootModel
from enum import Enum


class ConfigRange(str, Enum):
    """Configuration value ranges for validation"""
    TINY_INT = "tiny_int"
    SMALL_INT = "small_int"
    MEDIUM_INT = "medium_int"
    INTEGER = "integer"
    BIGINT = "bigint"


class LogLevel(str, Enum):
    """Logging level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration schema"""
    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = Field(default="default_db")
    user: str = Field(default="")
    password: str = Field(default="")

    model_config = ConfigDict(extra="allow", validate_assignment=True)


class RedisConfig(BaseModel):
    """Redis configuration schema"""
    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)

    model_config = ConfigDict(extra="allow", validate_assignment=True)


class LoggingConfig(BaseModel):
    """Logging configuration schema"""
    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file: Optional[str] = None

    model_config = ConfigDict(extra="allow", validate_assignment=True)


class PluginConfig(BaseModel):
    """Plugin configuration schema"""
    enabled: List[str] = Field(default_factory=list)
    paths: List[str] = Field(default_factory=list)
    auto_load: bool = Field(default=True)

    model_config = ConfigDict(extra="allow", validate_assignment=True)


# Alias for test compatibility
PluginsConfig = PluginConfig


class ConfigSchema(BaseModel):
    """
    Main configuration schema with validation

    Supports nested configurations with type validation,
    constraint checking, and clear error messages.
    """
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)

    # Additional dynamic fields can be added
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    @field_validator('*')
    @classmethod
    def validate_string_fields(cls, v: Any, info) -> Any:
        """Validate string fields to prevent injection"""
        if isinstance(v, str):
            # Basic SQL injection prevention
            dangerous_patterns = [';--', '/*', '*/', 'xp_', 'union', 'SELECT']
            v_lower = v.lower()
            for pattern in dangerous_patterns:
                if pattern in v_lower:
                    raise ValueError(f"Potentially dangerous pattern detected: {pattern}")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_logging(cls, model: 'ConfigSchema') -> 'ConfigSchema':
        """Validate logging configuration"""
        # Ensure log level is valid enum value
        if isinstance(model.logging, dict):
            if 'level' in model.logging:
                try:
                    model.logging['level'] = LogLevel(model.logging['level'])
                except ValueError:
                    raise ValueError(f"Invalid log level: {model.logging.get('level')}")
        return model
