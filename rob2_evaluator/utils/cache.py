"""缓存工具类"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from functools import wraps


class FileCache:
    """文件处理结果缓存类"""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件的SHA256哈希值"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_cache_path(self, file_hash: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{file_hash}.json"

    def get_cached_result(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """获取缓存的处理结果"""
        file_hash = self._get_file_hash(file_path)
        cache_path = self._get_cache_path(file_hash)

        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取缓存出错: {e}")
                return None
        return None

    def save_result(self, file_path: Path, result: Dict[str, Any]) -> None:
        """保存处理结果到缓存"""
        file_hash = self._get_file_hash(file_path)
        cache_path = self._get_cache_path(file_hash)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存出错: {e}")


def cache_result(cache_instance: Optional[FileCache] = None):
    """处理结果缓存装饰器"""
    if cache_instance is None:
        cache_instance = FileCache()

    def decorator(func):
        @wraps(func)
        def wrapper(self, input_path: Path, *args, **kwargs):
            # 尝试从缓存获取结果
            cached_result = cache_instance.get_cached_result(input_path)
            if cached_result is not None:
                print(f"使用缓存结果: {input_path}")
                return cached_result

            # 如果没有缓存，执行原函数并保存结果
            result = func(self, input_path, *args, **kwargs)
            cache_instance.save_result(input_path, result)
            return result

        return wrapper

    return decorator
