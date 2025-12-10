#!/usr/bin/env python3
"""测试应用程序导入"""

import sys
import os

print("开始测试应用程序导入...")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

try:
    # 添加/app到路径
    sys.path.insert(0, '/app')
    
    print("\n尝试导入应用程序...")
    from app import create_app
    
    print("✅ 应用程序导入成功")
    
    print("\n尝试创建应用程序实例...")
    app = create_app()
    print("✅ 应用程序创建成功")
    
    print("\n✅ 所有测试通过!")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成。")
