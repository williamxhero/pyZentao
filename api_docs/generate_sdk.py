#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据 OpenAPI 规范的 YAML 文件自动生成禅道 Python SDK

- 解析 api_docs/zentao_api_docs.yaml
- 生成 core/models 下的 dataclass 风格数据模型
- 生成 core/api 下的 API 分组类
- 生成 BaseAPI 和 BaseModel 基类
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

def main():
    project_root = Path(__file__).parent.parent
    yaml_file = project_root / "api_docs" / "zentao_api_docs.yaml"
    sdk_dir = project_root / "zentao_api"
    core_dir = sdk_dir / "core"
    api_dir = core_dir / "api"
    models_dir = core_dir / "models"

    sdk_dir.mkdir(exist_ok=True)
    core_dir.mkdir(exist_ok=True)
    api_dir.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)

    print("加载 OpenAPI 规范文档...")
    with open(yaml_file, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    schemas = spec.get("components", {}).get("schemas", {})
    paths = spec.get("paths", {})

    print(f"发现 {len(schemas)} 个数据模型定义，开始生成模型代码...")
    # 生成基类
    generate_base_model(models_dir)
    generate_base_api(api_dir)
    print("基础模型和基础API类生成完成。")

    # 生成模型
    model_names = set()
    for schema_name, schema_obj in schemas.items():
        print(f"生成模型: {schema_name}")
        code = generate_model_code(schema_name, schema_obj, schemas, model_names)
        with open(models_dir / f"{schema_name.lower()}.py", "w", encoding="utf-8") as f:
            f.write(code)

    # 生成 models/__init__.py
    print("生成 models/__init__.py ...")
    with open(models_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write('"""\n自动生成的禅道API数据模型\n"""\n')
        f.write('from .base import BaseModel\n')
        for name in sorted(model_names):
            f.write(f"from .{name.lower()} import {name}\n")
        f.write("\n__all__ = [\n")
        f.write("    'BaseModel',\n")
        for name in sorted(model_names):
            f.write(f"    '{name}',\n")
        f.write("]\n")

    # 生成 API 类
    groups = {}
    for path, item in paths.items():
        for method, meta in item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
            tags = meta.get("tags", [])
            if not tags:
                continue  # 没有tags的接口忽略
            tag = tags[0]
            groups.setdefault(tag, []).append((path, method.upper(), meta))

    print(f"发现 {len(groups)} 个API分组，开始生成API类...")
    api_class_names = []
    for tag, endpoints in groups.items():
        class_name = f"{tag.capitalize()}API"
        print(f"生成API类: {class_name}")
        api_class_names.append(class_name)
        code = generate_api_class_code(class_name, endpoints)
        with open(api_dir / f"{tag.lower()}.py", "w", encoding="utf-8") as f:
            f.write(code)

    # 生成 api/__init__.py
    print("生成 api/__init__.py ...")
    with open(api_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write('"""\n自动生成的禅道API接口类\n"""\n')
        f.write('from .base import BaseAPI\n')
        for cls in sorted(api_class_names):
            f.write(f"from .{cls[:-3].lower()} import {cls}\n")
        f.write("\n__all__ = [\n")
        f.write("    'BaseAPI',\n")
        for cls in sorted(api_class_names):
            f.write(f"    '{cls}',\n")
        f.write("]\n")

    print("SDK代码生成完成。")

def generate_base_model(models_dir: Path):
    code = '''"""
BaseModel 基类
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime, date

@dataclass
class BaseModel:
    """禅道API数据模型基类，支持序列化和反序列化"""

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        return cls(**data)
'''
    with open(models_dir / "base.py", "w", encoding="utf-8") as f:
        f.write(code)

def generate_base_api(api_dir: Path):
    code = '''"""
BaseAPI 基类
"""
from typing import Dict, Any, Optional
from ..client import ZentaoClient

class BaseAPI:
    """禅道API接口基类，封装异步请求逻辑"""

    def __init__(self, client: ZentaoClient):
        self.client = client

    async def _request(
        self,
        method: str,
        path: str,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Any:
        return await self.client._request(
            method=method,
            path=path,
            path_params=path_params,
            query_params=query_params,
            body=body
        )
'''
    with open(api_dir / "base.py", "w", encoding="utf-8") as f:
        f.write(code)

def generate_model_code(name: str, schema: Dict[str, Any], schemas: Dict[str, Any], model_names: Set[str]) -> str:
    model_names.add(name)
    required = schema.get("required", [])
    props = schema.get("properties", {})

    used_typing: Set[str] = set()
    used_datetime: Set[str] = set()

    lines = [
        '"""',
        f"{name} 数据模型",
        '"""',
        "from dataclasses import dataclass",
        "__IMPORT_PLACEHOLDER__",
        "from .base import BaseModel",
        "",
        "@dataclass",
        f"class {name}(BaseModel):",
        f'    """{name}"""'
    ]

    if not props:
        lines.append("    pass")
    else:
        # 先分组字段
        required_props = []
        optional_props = []
        for prop, info in props.items():
            if prop in required:
                required_props.append((prop, info))
            else:
                optional_props.append((prop, info))

        def process_props(prop_list, is_optional: bool):
            nonlocal used_typing, used_datetime
            for prop, info in prop_list:
                typ = "Any"
                if "$ref" in info:
                    ref_name = info["$ref"].split("/")[-1]
                    typ = ref_name
                    # 递归生成引用的模型
                    if ref_name not in model_names and ref_name in schemas:
                        nested_code = generate_model_code(ref_name, schemas[ref_name], schemas, model_names)
                        with open(Path(__file__).parent.parent / "zentao_api/core/models" / f"{ref_name.lower()}.py", "w", encoding="utf-8") as f:
                            f.write(nested_code)
                else:
                    t = info.get("type", "string")
                    if t == "string":
                        typ = "str"
                    elif t == "integer":
                        typ = "int"
                    elif t == "boolean":
                        typ = "bool"
                    elif t == "number":
                        typ = "float"
                    elif t == "array":
                        items = info.get("items", {})
                        if "$ref" in items:
                            item_ref = items["$ref"].split("/")[-1]
                            typ = f"List[{item_ref}]"
                            used_typing.add("List")
                            # 递归生成
                            if item_ref not in model_names and item_ref in schemas:
                                nested_code = generate_model_code(item_ref, schemas[item_ref], schemas, model_names)
                                with open(Path(__file__).parent.parent / "zentao_api/core/models" / f"{item_ref.lower()}.py", "w", encoding="utf-8") as f:
                                    f.write(nested_code)
                        else:
                            item_type = items.get("type", "Any")
                            if item_type == "string":
                                typ = "List[str]"
                            elif item_type == "integer":
                                typ = "List[int]"
                            elif item_type == "boolean":
                                typ = "List[bool]"
                            elif item_type == "number":
                                typ = "List[float]"
                            else:
                                typ = "List[Any]"
                            used_typing.add("List")
                    else:
                        typ = "Any"

                if is_optional:
                    typ = f"Optional[{typ}]"
                    used_typing.add("Optional")

                # 统计类型
                if "List" in typ:
                    used_typing.add("List")
                if "Dict" in typ:
                    used_typing.add("Dict")
                if "Any" in typ:
                    used_typing.add("Any")
                if "datetime" in typ:
                    used_datetime.add("datetime")
                if "date" in typ:
                    used_datetime.add("date")

                default = " = None" if is_optional else ""
                lines.append(f"    {prop}: {typ}{default}")

        # 先输出无默认值字段
        process_props(required_props, is_optional=False)
        # 再输出有默认值字段
        process_props(optional_props, is_optional=True)

    # 生成 imports
    import_lines = []
    if used_typing:
        import_lines.append(f"from typing import {', '.join(sorted(used_typing))}")
    if used_datetime:
        import_lines.append(f"from datetime import {', '.join(sorted(used_datetime))}")

    # 替换占位符
    import_block = "\n".join(import_lines)
    lines = [line if line != "__IMPORT_PLACEHOLDER__" else import_block for line in lines]

    return "\n".join(lines)

def generate_api_class_code(class_name: str, endpoints: List):
    model_imports = set()
    typing_imports = set()

    lines = [
        '"""',
        f"{class_name} 自动生成的API接口类",
        '"""',
        "from .base import BaseAPI",
        ""
    ]

    # 添加类定义
    lines.append(f"class {class_name}(BaseAPI):")
    lines.append(f'    """{class_name}"""')
    lines.append("")

    indent1 = "    "
    indent2 = "        "
    indent3 = "            "
    indent4 = "                "

    for path, method, meta in endpoints:
        func_name = meta.get("operationId") or path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        summary = meta.get("summary", "")
        params = []
        param_lines = []
        path_params_list = []

        # 处理参数
        for param in meta.get("parameters", []):
            pname = param.get("name")
            if pname.lower() == "token":
                continue  # 不生成Token参数
            prequired = param.get("required", False)
            ptype = "Any"
            schema = param.get("schema", {})
            t = schema.get("type", "string")
            if t == "string":
                ptype = "str"
            elif t == "integer":
                ptype = "int"
            elif t == "boolean":
                ptype = "bool"
            elif t == "number":
                ptype = "float"
            else:
                ptype = "Any"
            default = "" if prequired else " = None"

            # 路径参数
            if param.get("in") == "path":
                params.append(f"{pname}: {ptype}")
                param_lines.append(f"{indent3}{pname}: 路径参数")
                path_params_list.append(pname)
            else:
                params.append(f"{pname}: Optional[{ptype}]{default}")
                param_lines.append(f"{indent3}{pname}: {param.get('description', '')}")
                typing_imports.add("Optional")

            if not prequired:
                typing_imports.add("Optional")
            if ptype == "Any":
                typing_imports.add("Any")

        # 请求体参数
        has_body = False
        request_body = meta.get("requestBody", {})
        content = request_body.get("content", {})
        if "application/json" in content:
            has_body = True
            schema = content["application/json"].get("schema", {})
            params.append("body: Optional[Dict[str, Any]] = None")
            param_lines.append(f"{indent3}body: 请求体参数")
            typing_imports.update(["Optional", "Dict", "Any"])

        # 推断返回类型
        responses = meta.get("responses", {})
        return_type = "Any"
        if "200" in responses:
            resp = responses["200"]
            content = resp.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                if "$ref" in schema:
                    return_type = schema["$ref"].split("/")[-1]
                    model_imports.add(return_type)
                else:
                    return_type = "Any"
                    typing_imports.add("Any")
        else:
            typing_imports.add("Any")

        param_str = ", ".join(params)
        lines.append(f"{indent1}async def {func_name}(self, {param_str}) -> {return_type}:")
        lines.append(f'{indent2}"""{summary}')
        lines.append("")
        lines.append(f"{indent2}Args:")
        lines.extend(param_lines)
        lines.append("")
        lines.append(f"{indent2}Returns:")
        lines.append(f"{indent3}{return_type} 响应模型")
        lines.append(f'{indent2}"""')
        lines.append(f"{indent2}return await self._request(")
        lines.append(f'{indent3}method=\"{method}\",')
        lines.append(f'{indent3}path=f\"{path}\",')
        # 生成path_params字典
        if path_params_list:
            lines.append(f"{indent3}path_params={{")
            for pname in path_params_list:
                lines.append(f'{indent4}"{pname}": {pname},')
            lines.append(f"{indent3}}},")
        else:
            lines.append(f"{indent3}path_params=None,")
        lines.append(f"{indent3}query_params=None,")
        if has_body:
            lines.append(f"{indent3}body=body")
        else:
            lines.append(f"{indent3}body=None")
        lines.append(f"{indent2})\n")

    # 在顶部添加 typing imports
    if typing_imports:
        import_line = "from typing import " + ", ".join(sorted(typing_imports))
        lines.insert(4, import_line)

    # 在顶部添加模型 imports
    if model_imports:
        import_line = "from ..models import " + ", ".join(sorted(model_imports))
        lines.insert(4, import_line)

    return "\n".join(lines)

if __name__ == "__main__":
    main()
