# Hex to EXE/DATA Converter

这个脚本用于将类似 `1.in` 的十六进制内存转储文件转换为两个文件：
- `.exe` 文件：所有内存内容，以指令格式呈现
- `.data` 文件：所有内存内容，以数据格式呈现

**重要设计理念**：内存中的内容既可能是指令也可能是数据，因此两个文件包含完全相同的内存内容，只是格式不同。这样可以支持：
- CPU 从 `.exe` 文件按 PC 取指令
- 内存访问操作从 `.data` 文件读写数据
- 自修改代码等特殊情况

## 输入格式

输入文件格式如下：
```
@ADDRESS
HEX HEX HEX ...
@ADDRESS
HEX HEX HEX ...
```

例如：
```
@00000000
37 01 02 00 EF 10 00 04 13 05 F0 0F 
@00001000
37 17 00 00 83 27 07 1B 33 45 F5 00 
```

## 字节序

**重要**: 该脚本默认使用**小端序** (Little-Endian)，这是 RISC-V 的标准字节序。

例如，hex 文件中的 `37 01 02 00` 会被解析为 32 位字 `0x00020137`。

如果你的 hex 文件使用大端序，请使用 `--big-endian` 选项。

## 内存填充

脚本会自动用 0 填充跳过的内存区域。例如，如果有：
- 代码段：`0x0000` - `0x0018` 
- 数据段：`0x1000` - `0x11A0`

那么输出文件会包含从 `0x0000` 到 `0x11A0` 的完整内存内容，其中 `0x0018` 到 `0x1000` 之间会被填充为 0。

## 使用方法

### 基本用法（自动检测内存范围）

```bash
python3 hex_to_exe_data.py 1.in -o output
```

这将：
- 自动检测内存起始和结束地址
- 生成 `output.exe`（所有内存内容，以指令格式）
- 生成 `output.data`（所有内存内容，以数据格式）
- 用 0 填充内存间隙

### 手动指定内存范围

如果需要扩展或限制内存范围：

```bash
python3 hex_to_exe_data.py 1.in -o output \
    --start 0x0 \
    --end 0x2000
```

### 使用大端序

```bash
python3 hex_to_exe_data.py input.hex -o output --big-endian
```

## 输出格式

两个输出文件包含相同的内存内容，只是格式不同。

### .exe 文件格式

每行一条 32 位指令，带注释显示地址：
```
00020137 //  0: instruction
040010ef //  4: instruction
0ff00513 //  8: instruction
00000000 // 12: instruction  ← 填充的零
...
00001737 // 4096: instruction  ← 0x1000 处的内容
```

### .data 文件格式

每行一个十六进制数值（无 0x 前缀，最小位数表示）：
```
20137
40010ef
ff00513
0           ← 填充的零
...
1737        ← 0x1000 处的内容
```

## 命令行选项

- `input`: 输入的 hex 文件路径（必需）
- `-o, --output-base`: 输出文件的基础名称（默认: "output"）
- `--start`: 内存起始地址（十六进制或十进制）。不指定则自动检测。
- `--end`: 内存结束地址（十六进制或十进制）。不指定则自动检测。
- `--little-endian`: 使用小端序（默认，RISC-V 标准）
- `--big-endian`: 使用大端序

## 示例

将 `1.in` 转换为 `program.exe` 和 `program.data`:
```bash
python3 hex_to_exe_data.py 1.in -o program
```

查看帮助信息：
```bash
python3 hex_to_exe_data.py --help
```
