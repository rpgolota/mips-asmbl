# masmbl

**Customizable and extendable simple mips assembler**

Simple to change or add instructions.

---

## Installation

#### Clone this repository and install masmbl
`pip install .`

---

## Running

`masmbl <INPUT_MIPS> -d/--data <OUTPUT_DATA> -i/--instruction <OUTPUT_INSTRUCTIONS>`
Optional arguments:
- [-v | --verbose] verbose
- [-c | --config] yaml file that specifies language. Extend default.yaml in masmbl source folder.
- [-b | --binary] output binary instead of hex data and instructions

---

## Customize and Extend

Changing the yaml file and using it will allow to create custom instructions whose assembly can be specified.
- Use `instruction_input` section to specify what format input this new instruction should expect
  - Use `special_parsers` to specify capture of regex groups that are for special syntax. An example is the lw/sw instructions in default.yaml
- Use `instruction_output` to specify how to output assembled instruction should look, using the same tokens as in `instruction_input`
  - Also possible to directly specify number in a slot using `bXX...` where the `X` are binary digits 0 and 1

Making new pseudo-instructions is similar
- Use `pseudoinstruction_input` to specify name and expected format of the input for the pseudo-instruction
- Use `pseudoinstruction_output` to specify the instruction or instructions the pseudo-instruction should expand into
  - If a pseudo-instruction takes an input named `one`, to expand it in the output use % signs like so: `%one%`

---

## Notes

- This simple assembler expects a `.data` segment if it exists as the very first segment.
- You must label `.text` before starting to write code, as it is needed to separate the sections for this simple program
- Most all else is robust to code style, though this assembler does not strictly follow any mips specification closely