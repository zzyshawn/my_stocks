"""测试客户端

用于验证 IPC 服务流程正确性 - 支持简化响应格式
"""
import json
import time
import sys
from pathlib import Path
from multiprocessing.connection import Client


def create_test_data():
    """创建测试数据"""
    test_data = {
        'account_summary': {
            'total_assets': 100000.0,
            'available_funds': 100000.0,
            'frozen_funds': 0.0,
            'daily_pnl': 0.0,
            'daily_pnl_pct': 0.0,
            'total_market_value': 0.0,
            'holdings': {},
            'updated_at': '2026-03-29T10:00:00'
        },
        'realtime_data': {
            'timestamp': '2026-03-29T10:30:00',
            'market_status': 'trading',
            'stocks': [
                {
                    'symbol': '000001.SZ',
                    'name': '平安银行',
                    'current_price': 11.2,
                    'change': 0.25,
                    'change_pct': 2.28,
                    'open': 10.95,
                    'high': 11.35,
                    'low': 10.90,
                    'volume': 1250000,
                    'turnover': 14000000.0,
                    'pe_ratio': 6.5,
                    'pb_ratio': 0.85,
                    'timestamp': '2026-03-29T10:30:00',
                    'indicators': {'MA5': 10.98, 'RSI': 62.5}
                },
                {
                    'symbol': '600519.SH',
                    'name': '贵州茅台',
                    'current_price': 1720.0,
                    'change': 25.0,
                    'change_pct': 1.47,
                    'open': 1695.0,
                    'high': 1735.0,
                    'low': 1690.0,
                    'volume': 25000,
                    'turnover': 43000000.0,
                    'pe_ratio': 28.5,
                    'pb_ratio': 8.2,
                    'timestamp': '2026-03-29T10:30:00',
                    'indicators': {'MA5': 1705.0, 'RSI': 58.0}
                }
            ],
            'extra_data': {}
        }
    }

    # 保存测试数据
    data_path = Path('tests/fixtures/sample_ipc_request.json')
    data_path.parent.mkdir(parents=True, exist_ok=True)

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    return str(data_path)


def print_analysis_result(response: dict):
    """打印分析结果（简化格式）"""
    print("\n  分析结果:")
    print(f"  {'─' * 56}")

    # 账户信息
    account = response.get('account', {})
    print(f"  💰 账户可用余额: {account.get('available_balance', 0):,.2f} 元")
    print()

    # 持仓列表
    positions = response.get('positions', [])
    if positions:
        print(f"  📊 持仓情况 ({len(positions)} 只股票):")
        print(f"  {'─' * 56}")
        for i, pos in enumerate(positions, 1):
            print(f"  [{i}] {pos['stock_code']}")
            print(f"      持仓数量: {pos['hold_quantity']} 股")
            print(f"      成本价: {pos['cost']:.2f} 元")
            print(f"      操作建议: {pos['operation']}", end="")
            if pos['operation_quantity'] > 0:
                print(f" {pos['operation_quantity']} 股")
            else:
                print()
            print(f"      理由: {pos['reason'][:50]}...")
            print()
    else:
        print("  📊 无持仓")


def test_single_request(conn, data_path, user_id='test_user'):
    """测试单次请求"""
    print("\n" + "=" * 60)
    print("测试 1: 发送分析请求")
    print("=" * 60)

    # 发送数据就绪信号
    request = {
        'type': 'DATA_READY',
        'data_path': data_path,
        'user_id': user_id,
        'conversation_id': 'test_conv'
    }

    print(f"[*] 发送: {request['type']}")
    print(f"[*] 用户ID: {user_id}")
    print(f"[*] 数据路径: {data_path}")

    conn.send(request)

    # 等待完成
    print("[*] 等待分析完成...")
    response = conn.recv()

    print(f"\n[+] 收到响应: {response.get('type')}")

    if response.get('type') == 'ANALYSIS_DONE':
        print("[+] 分析成功!")
        print_analysis_result(response)
        return True
    else:
        print(f"[!] 错误: {response.get('error')}")
        return False


def test_multiple_requests(conn, data_path):
    """测试多次请求（验证账户持久化）"""
    print("\n" + "=" * 60)
    print("测试 2: 连续多次请求（验证账户持久化）")
    print("=" * 60)

    results = []
    user_id = 'test_user_multi'

    for i in range(3):
        print(f"\n[*] 第 {i+1} 轮请求...")

        request = {
            'type': 'DATA_READY',
            'data_path': data_path,
            'user_id': user_id,
            'conversation_id': 'test_conv'
        }

        conn.send(request)
        response = conn.recv()

        if response.get('type') == 'ANALYSIS_DONE':
            account = response.get('account', {})
            positions = response.get('positions', [])
            print(f"[+] 第 {i+1} 轮完成")
            print(f"    可用余额: {account.get('available_balance', 0):,.2f}")
            print(f"    持仓数: {len(positions)}")
            results.append(True)
        else:
            print(f"[!] 第 {i+1} 轮失败: {response.get('error')}")
            results.append(False)

        time.sleep(0.5)

    success = sum(results)
    print(f"\n[*] {success}/{len(results)} 轮成功")
    return success == len(results)


def test_error_handling(conn):
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试 3: 错误处理（不存在的文件）")
    print("=" * 60)

    request = {
        'type': 'DATA_READY',
        'data_path': 'nonexistent_file.json',
        'user_id': 'test_user',
        'conversation_id': 'test_conv'
    }

    print("[*] 发送请求（文件不存在）...")
    conn.send(request)
    response = conn.recv()

    print(f"[+] 收到响应: {response.get('type')}")

    if response.get('type') == 'ERROR':
        print(f"[+] 正确返回错误: {response.get('error')}")
        return True
    else:
        print("[!] 应该返回错误但没有")
        return False


def test_unknown_message(conn):
    """测试未知消息类型"""
    print("\n" + "=" * 60)
    print("测试 4: 未知消息类型处理")
    print("=" * 60)

    request = {
        'type': 'UNKNOWN_COMMAND'
    }

    print("[*] 发送未知消息类型...")
    conn.send(request)
    response = conn.recv()

    print(f"[+] 收到响应: {response.get('type')}")

    if response.get('type') == 'ERROR':
        print(f"[+] 正确返回错误: {response.get('error')}")
        return True
    else:
        print("[!] 应该返回错误但没有")
        return False


def test_stop(conn):
    """测试停止服务"""
    print("\n" + "=" * 60)
    print("测试 5: 发送停止信号")
    print("=" * 60)

    print("[*] 发送 STOP 信号...")
    conn.send({'type': 'STOP'})

    response = conn.recv()
    print(f"[+] 收到响应: {response.get('type')}")

    return response.get('type') == 'STOPPED'


def main():
    """主函数"""
    print("=" * 60)
    print("测试客户端 - 股票分析Agent IPC服务")
    print("=" * 60)

    # 创建测试数据
    print("\n[*] 创建测试数据...")
    data_path = create_test_data()
    print(f"[+] 测试数据: {data_path}")

    # 连接服务
    print("\n[*] 连接服务 localhost:6000...")
    try:
        conn = Client(('localhost', 6000), authkey=b'secret')
        print("[+] 连接成功")
    except Exception as e:
        print(f"[!] 连接失败: {e}")
        print("[*] 请先启动服务: python run_service.py")
        return 1

    # 执行测试
    results = []

    try:
        # 测试 1: 单次请求
        results.append(('单次请求', test_single_request(conn, data_path)))

        # 测试 2: 多次请求（账户持久化）
        results.append(('连续请求', test_multiple_requests(conn, data_path)))

        # 测试 3: 错误处理
        results.append(('错误处理', test_error_handling(conn)))

        # 测试 4: 未知消息
        results.append(('未知消息', test_unknown_message(conn)))

        # 测试 5: 停止服务
        results.append(('停止服务', test_stop(conn)))

    except Exception as e:
        print(f"\n[!] 测试异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"{name}: {status}")

    all_passed = all(ok for _, ok in results)
    print("\n" + ("全部测试通过!" if all_passed else "部分测试失败!"))

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
