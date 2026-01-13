## Principles
- Be concise, keep it simple
- Descriptive variable names
- Don't assume, assess
- Ask questions

## Inner workings
- Use standard diff format. Do not use unified diffs with context lines unless necessary for disambiguation.
- Do not explain code unless asked. Do not summarize changes. Output only the diff or the file content.
- Use parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.

## Tools
- Always prioritize using faster tools such as `fd` and `rg` over slower alternatives like `find` and `grep`.
