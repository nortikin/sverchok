import sys

if __name__ == "__main__":
    try:
        from sverchok.utils.apidoc import generate_api_documentation
        generate_api_documentation("/tmp/doc")
    except Exception as e:
        print(e)
        sys.exit(1)

