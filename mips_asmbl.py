import yaml
from pprint import pprint
import re
from bitstring import Bits
import argparse

def convert_register(regstr):
    
    REGS = {
        "$zero": 0,
        "$at": 1,
        "$v0": 2,
        "$v1": 3,
        "$a0": 4,
        "$a1": 5,
        "$a2": 6,
        "$a3": 7,
        "$t0": 8,
        "$t1": 9,
        "$t2": 10,
        "$t3": 11,
        "$t4": 12,
        "$t5": 13,
        "$t6": 14,
        "$t7": 15,
        "$s0": 16,
        "$s1": 17,
        "$s2": 18,
        "$s3": 19,
        "$s4": 20,
        "$s5": 21,
        "$s6": 22,
        "$s7": 23,
        "$t8": 24,
        "$t9": 25,
        "$k0": 26,
        "$k1": 27,
        "$gp": 28,
        "$sp": 29,
        "$fp": 30,
        "$ra": 31,
    }
    
    converted = REGS.get(regstr, None)
    converted = REGS.get("$" + regstr, None) if converted is None else converted
    if converted is None:
        t = None
        if regstr.startswith("$"):
            t = regstr[1:]
        else:
            t = regstr
            
        try:
            converted = int(t)
        except:
            converted = None
            
    if converted is None:
        raise ValueError(f"[ERROR] Could not convert {regstr} into a register value.")
    
    return converted

def verify_instruction_format(instr_format):
    
    fields = instr_format["fields"]
    inp = instr_format["instruction_input"]
    out = instr_format["instruction_output"]

    is_number = lambda s: s.startswith("b") and all(str.isdigit(c) for c in s[1:])
    in_field  = lambda s: s in fields
    
    for instr, format in out.items():
        
        total = 0
        for item in format:
            if is_number(item):
                total += len(item) - 1
            elif in_field(item):
                loc = fields[item][0]
                total += loc[0] - loc[1] + 1
            else:
                raise ValueError(f"[ERROR] When validating instruction output {instr}, format item {item} is not a number and is not declared in fields.")
        
        if total != 32:
            raise ValueError(f"[ERROR] The instruction {instr} in instruction_output has total bit size of {total} != 32.")

def split_line(line):
    
    if "#" in line:
        line = line[:line.find("#")]
    
    line = line.strip()
    
    line = line.split()
    line_split = []
    for i in line:
        c = [b for b in i.split(",") if b]
        line_split += c
        
    return line_split

def split_lines(mips_lines):
    final = []
    
    for line in mips_lines:
        res = split_line(line)
        
        if res:
            final.append(res)
            
    return final

def process_data(data, verbose):
    
    
    
    data = data[1:]
    newdata = []
    labels = {}

    for line in data:
        if line[0] == ".word":
            newdata += line[1:]
        else:
            
            if verbose:
                print(f"       - Found a label {line[0][:-1]:10s} at index {len(newdata):5d} = byteindex {len(newdata) * 4:6d}")
            
            labels[line[0][:-1]] = len(newdata) * 4
            if not line[1:]:
                continue
            elif line[1] == ".word":
                newdata += line[2:]
                
    return newdata, labels



def parse_instruction(instrformat, instruction, datalabels):
    
    instr_in = instrformat["instruction_input"][instruction[0]]
    instr_out = instrformat["instruction_output"][instruction[0]]
    
    if len(instr_in) != len(instruction[1:]):
        raise ValueError(f"[ERROR] Instruction {instruction[0]} does not match the input format. Expected {instr_in}, got {instruction[1:]}.")
    
    usable_instr = instruction[1:]
    instr = instr_out.copy()
    
    i = 0
    while i < len(instr_in):
        expected_input = instr_in[i]
        
        if type(expected_input) is dict:
            if len(expected_input) != 1:
                raise ValueError(f"[ERROR] Expected a size 1 dictionary as special syntax descriptor: {expected_input}")
            key = list(expected_input.keys())[0]
            item = expected_input[key]
            special = instrformat["special_parsers"][key]
            search = special["re"]
            types = special["output"]
            
            res = re.search(search, usable_instr[i]).groups()
            if len(res) != len(types):
                raise ValueError(f"[ERROR] Special parsing found {len(res)} components: {res}, but expected {len(types)}.")
            
            fin = []
            for t, r in zip(types, res):
                q = None
                if t == "register":
                    q = convert_register(r)
                elif t == "number":
                    q = int(r, 0)
                elif t == "label":
                    q = datalabels(r)
                fin.append(q)
            
            for t, r in zip(item, fin):
                field_data = instrformat["fields"][t]
                width = field_data[0][0] - field_data[0][1] + 1
                
                if type(r) is int:
                    orig = r
                    r = f"{r:b}"
                    if len(r) > width:
                        print(f"[WARNING] Instruction {instruction} field {i}: {usable_instr[i]} results in a bit width {len(r)} > {width}, the allowed width.")
                    r = "b" + Bits(int=orig, length=32).bin[-1 * width:]
                else:
                    raise ValueError(f"[ERROR] Unknown type in special parser: {t}.")
                
                loc = instr.index(t)
                instr[loc] = r
            
        else:
            field_data = instrformat["fields"][expected_input]
            input_type = field_data[1]["input"]
            width = field_data[0][0] - field_data[0][1] + 1
            
            r = None
            if type(input_type) is not list:
                input_type = [input_type]

            if "register" in input_type and usable_instr[i].startswith("$"):
                r = convert_register(usable_instr[i])
            elif "number" in input_type and (str.isnumeric(usable_instr[i]) or str.isnumeric(usable_instr[i][1:]) or (re.fullmatch(r"0x[0-9a-fA-F]+", usable_instr[i]) is not None)):
                r = int(usable_instr[i], 0)
            elif usable_instr[i] in datalabels:
                r = datalabels[usable_instr[i]]
            elif not str.isidentifier(usable_instr[i]):
                raise ValueError(f"[ERROR] Unknown instruction component when parsing {instruction}: {usable_instr[i]}")
        
            if type(r) is int:
                orig = r
                r = f"{r:b}"
                if len(r) > width:
                    print(f"[WARNING] Instruction {instruction} field {i}: {usable_instr[i]} results in a bit width {len(r)} > {width}, the allowed width.")
                r = "b" + Bits(int=orig, length=32).bin[-1 * width:]
            else:
                r = {usable_instr[i]: width}
            
            loc = instr.index(expected_input)
            instr[loc] = r
        
        i += 1
    
    return instr

def parse_pseudoinstruction(instrformat, instruction, datalabels):
    
    name = instruction[0]
    instruction = instruction[1:]
    instr_in = instrformat["pseudoinstruction_input"][name]
    instr_out = instrformat["pseudoinstruction_output"][name]

    def replace_all(find, replace):
        nonlocal instr_out
        new = []
        for i in instr_out:
            new.append(i.replace(f"%{find}%", replace))
            
        instr_out = new
                
    
    if len(instruction) != len(instr_in):
        raise ValueError(f"[ERROR] Pseudo-instruction {name} does not match the input format. Expected {instr_in}, got {instruction}.")
    
    for fmt, real in zip(instr_in, instruction):
        ref = list(fmt.keys())[0]
        ty = fmt[ref]
        
        val = None
        if ty == "register":
            val = convert_register(real)
        elif ty == "number":
            val = int(real, 0)
        elif ty == "label":
            val = datalabels[real]
            
        if val is None:
            raise ValueError(f"[ERROR] Invalid type for pseudo-instruction: {ty}")

        replace_all(ref, real)
    
    instr_out = split_lines(instr_out)
    res = [parse_instruction(instrformat, l, datalabels) for l in instr_out]
    
    return res, len(res)

# expects .globl <label> as the second thing after .text
def process_instructions(instructions, datalabels, instrformat, verbose):
    instr_i = 0
    
    instructions = instructions[1:]
    labels = {}

    output = []
    for line in instructions:
        if ".text" in line or ".globl" in line:
            continue
        elif line[0].endswith(":"):
                
            if verbose:
                print(f"       - Found a label {line[0][:-1]:10s} at index {instr_i:5d}")
            
            labels[line[0][:-1]] = instr_i
            if not line[1:]:
                continue
            elif line[1] in instrformat["instruction_input"]:
                
                if verbose:
                    print(f"       - Found instruction {line[1]}")
                
                output.append(parse_instruction(instrformat, line[1:], datalabels))
                instr_i += 1
            elif line[1] in instrformat["pseudoinstruction_input"]:
                
                if verbose:
                    print(f"       - Found pseudo-instruction {line[1]}")
                
                o, i = parse_pseudoinstruction(instrformat, line[1:], datalabels)
                output += o
                instr_i += i
            else:
                raise ValueError(f"[ERROR] Label followed by non-instruction: {line}.")
        elif line[0] in instrformat["instruction_input"]:
            
            if verbose:
                    print(f"       - Found instruction {line[0]}")
            
            output.append(parse_instruction(instrformat, line, datalabels))
            instr_i += 1
        elif line[0] in instrformat["pseudoinstruction_input"]:
            
            if verbose:
                    print(f"       - Found pseudo-instruction {line[1]}")
            
            o, i = parse_pseudoinstruction(instrformat, line, datalabels)
            output += o
            instr_i += i
        else:
            raise ValueError(f"[ERROR] Unexpected line: {line}")
    
    if verbose:
        print(f"[LOG] Giving values to text section labels.")
    
    final_output = []
    cur = 0
    for i in output:
        newi = []
        for c in i:
            if type(c) is dict:
                key = list(c.keys())[0]
                width = c[key]
                myindex = cur + 1
                index = labels[key]
                if width == 16:
                    num = index - myindex
                    b = "b" + Bits(int=num, length=16).bin
                    
                    if verbose:
                        print(f"       - Found offset-like label for instruction at index {cur:5d},      offset is {num:5d}")
                    
                elif width == 26:
                    num = index
                    b = "b" + Bits(int=num, length=26).bin
                    
                    if verbose:
                        print(f"       - Found value-like  label for instruction at index {cur:5d}, label value is {num:5d}")
                else:
                    raise ValueError(f"[ERROR] Uknown width of {width} left over as residue")
                newi.append(b)
            else:
                newi.append(c)
        final_output.append(newi)
        cur += 1
        
    return final_output, labels

def splice_words(wordlist):
    out = []
    
    for word in wordlist:
        t = ""
        for part in word:
            t += part[1:]
        out.append(t)
            
    return out

def splice_data(data):
    out = []
    
    for d in data:
        b = Bits(int=int(d), length=32).bin
        out.append(b)
    
    return out

def parse_file(format, mips_lines, verbose):
    
    if verbose:
        print(f"[LOG] Splitting mips file into lines.")
    
    lines = split_lines(mips_lines)
    
    in_any = lambda x: any(x in l for l in lines)
    
    if in_any(".data") and ".data" not in lines[0]:
        raise ValueError("[ERROR] This program expects the data section to come first and end before any code in the text section.")
    
    text_index = next(i for i, l in enumerate(lines) if ".text" in l)
    
    if verbose:
        print(f"[LOG] Splitting mips file data and text sections.")
    
    data = lines[0:text_index]
    instructions = lines[text_index:]
    
    if verbose:
        print(f"[LOG] Processing data to extract labels.")
    
    data, datalabels = process_data(data, verbose)
    
    if verbose:
        print(f"[LOG] Processing instructions.")
    
    instr, instrlabels = process_instructions(instructions, datalabels, format, verbose)
    
    if verbose:
        print(f"[LOG] Splicing data into bitstrings.")
    
    data = splice_data(data)
    
    if verbose:
        print(f"[LOG] Splicing instructions into bitstrings.")
    
    instr = splice_words(instr)
    
    return (data, instr), (datalabels, instrlabels)

def preprocess(mips):
    spl = mips.split("%")
    if len(spl) == 1:
        return mips
    res = []
    for s in spl:
        try:
            res.append(str(eval(s)))
        except:
            res.append(s)
        
    return "".join(res)

def assemble(args):
    
    to_assemble = args.input

    if args.verbose:
        print(f"[LOG] Opening language file {args.config} for reading.")

    with open(args.config, "r") as f:
        instructions = yaml.load(f, yaml.Loader)
    
    verify_instruction_format(instructions)
    
    if args.verbose:
        print(f"[LOG] Opening assembly file {args.input} for reading.")
    
    with open(to_assemble, "r") as f:
        mips = f.read().strip()
        if args.verbose:
            print(f"[LOG] Preprocessing {args.input}.")
        mips = preprocess(mips)
        mips = mips.split("\n")
        
    if args.verbose:
        print(f"[LOG] Starting to parse mips.")
    
    (data, instr), (datalabels, instrlabels) = parse_file(instructions, mips, args.verbose)
    
    if args.verbose:
        print(f"[LOG] Done assembling, starting to write output files.")
        print(f"[LOG] Writing data file {args.data}.")
    
    with open(args.data, "w") as f:
        for d in data:
            if args.binary:
                f.write(f"{int(d, 2):032b}\n")
            else:
                f.write(f"{int(d, 2):08x}\n")
    
    if args.verbose:
        print(f"[LOG] Writing instruction file {args.instruction}.")
    
    with open(args.instruction, "w") as f:
        for i in instr:
            if args.binary:
                f.write(f"{int(i, 2):032b}\n")
            else:
                f.write(f"{int(i, 2):08x}\n")
            
    if args.verbose:
        print(f"[LOG] Done writing. Showing the collected data and instruction label data.")
        print(f"[LOG] Data labels with byte addressing:")
        pprint(datalabels)
        print(f"\n[LOG] Instruction labels with 32 bit word addressing:")
        pprint(instrlabels)
        
    
def get_args():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("input")
    parser.add_argument("-d", "--data", nargs=1, required=True, help="data file output")
    parser.add_argument("-i", "--instruction", nargs=1, required=True, help="instruction file output")
    parser.add_argument("-c", "--config", nargs=1, default=["instructions.yaml"], help="choose a different language configuration file")
    parser.add_argument("-b", "--binary", action="store_true", help="output binary instead of hex")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
    
    args = parser.parse_args()
    args.instruction = args.instruction[0]
    args.data = args.data[0]
    args.config = args.config[0]
    
    return args    

def main():
    
    args = get_args()
    
    assemble(args)
    
if __name__ == "__main__":
    main()