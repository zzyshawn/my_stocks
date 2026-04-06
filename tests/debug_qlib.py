import sys
sys.path.insert(0, r"D:\code\qlib")

try:
    import qlib
    print("qlib imported successfully")
except Exception as e:
    print(f"Error importing qlib: {e}")

try:
    from qlib.data.dump_bin import DumpDataAll
    print("DumpDataAll imported successfully")
except Exception as e:
    print(f"Error importing DumpDataAll: {e}")
