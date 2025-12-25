# AST Node Reference

Each AST node has:  
- `kind` — node type (grammar construct)  
- `value` — optional payload (identifier name, literal, operator, etc.)  
- `children` — list of sub-nodes  

---

## program
```
program
└─ function+
```
- **children**: one or more `function` nodes  
- **value**: None

## function
```
function (value=name)
├─ params?
├─ general_statement*
└─ return_statement?'
```
- **children**: optional `params`, zero or more `general_statement`, optional `return_statement`  
- **value**: function name (string)

## params
```
params
└─ id*
```
- **children**: identifiers  
- **value**: None

## general_statement
```
general_statement
└─ output_statement | ... (other statements)
```
- **children**: one statement node  
- **value**: None

## output_statement
```
output_statement
└─ str_literal | id
```
- **children**: one literal or identifier  
- **value**: None

## return_statement
```
return_statement
└─ expr
```
- **children**: one expression node  
- **value**: None

## Expressions / Operators
```
| - | * | / | // | ** | == | != | > | >= | < | <= | and | or | !
├─ left_expr
└─ right_expr
```
- **children**: left and right operands  
- **value**: None

## function_call
```
function_call (value=name)
└─ arg*
```
- **children**: argument expressions  
- **value**: function name

## index
```
index
├─ id | function_call
└─ expr+
```
- **children**: base node + one or more index expressions  
- **value**: None

## Literals
- `int_literal` / `float_literal` / `str_literal` / `bool_literal`  
- **children**: None  
- **value**: literal value
