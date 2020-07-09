def make_version_string(version_info):
    """
    Turn a version tuple in to a version string, taking in to account any pre,
    post, and dev release tags, formatted according to PEP 440.
    """

    version_info = list(version_info)

    numbers = []
    while version_info and isinstance(version_info[0], int):
        numbers.append(str(version_info.pop(0)))
    version_str = '.'.join(numbers)

    if not version_info:
        return version_str

    assert len(version_info) % 2 == 0
    while version_info:
        suffix_type = version_info.pop(0)
        suffix_number = version_info.pop(0)

        if suffix_type in {'a', 'b', 'rc'}:
            suffix = f'{suffix_type}{suffix_number}'
        elif suffix_type in {'dev', 'post'}:
            suffix = f'.{suffix_type}{suffix_number}'
        else:
            raise ValueError(f"Unknown suffix type '{suffix_type}'")
        version_str += suffix

    return version_str


version_info = (0, 3, 0)
version_str = make_version_string(version_info)
