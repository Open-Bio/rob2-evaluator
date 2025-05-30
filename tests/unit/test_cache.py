"""测试缓存系统"""

import json
from pathlib import Path
import pytest
from rob2_evaluator.utils.cache import FileCache


def test_file_cache_creation(tmp_path):
    """测试缓存目录创建"""
    cache = FileCache(str(tmp_path / "test_cache"))
    assert cache.cache_dir.exists()
    assert cache.cache_dir.is_dir()


def test_file_hash_consistency(tmp_path):
    """测试文件哈希值的一致性"""
    cache = FileCache(str(tmp_path / "test_cache"))

    # 创建测试文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # 确保同一文件产生相同的哈希值
    hash1 = cache._get_file_hash(test_file)
    hash2 = cache._get_file_hash(test_file)
    assert hash1 == hash2


def test_cache_save_and_retrieve(tmp_path):
    """测试缓存的保存和检索"""
    cache = FileCache(str(tmp_path / "test_cache"))

    # 创建测试文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # 测试数据
    test_data = {"key": "value"}

    # 保存数据到缓存
    cache.save_result(test_file, test_data)

    # 检索缓存的数据
    retrieved_data = cache.get_cached_result(test_file)
    assert retrieved_data == test_data


def test_cache_invalid_file(tmp_path):
    """测试处理不存在的文件"""
    cache = FileCache(str(tmp_path / "test_cache"))
    non_existent_file = tmp_path / "non_existent.txt"

    with pytest.raises(FileNotFoundError):
        cache.get_cached_result(non_existent_file)
