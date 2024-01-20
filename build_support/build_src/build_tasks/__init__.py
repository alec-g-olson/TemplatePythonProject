"""Package for all build tasks.

- Common tasks cannot depend on any domain specific tasks.
- Combined tasks are allowed to depend on domain specific tasks.
- If a domain specific task depends on another domain or a combined task
then it is not domain specific and should be moved to combined tasks.
- Domain specific tasks can depend on common tasks.
"""
