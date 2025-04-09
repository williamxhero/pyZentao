#!/usr/bin/env python
"""
生成禅道 API SDK

此脚本用于根据 API 文档生成禅道 SDK 代码。
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

def generate_model_class(model_name: str, fields: List[Dict[str, Any]], model_classes: Set[str], nested_models: Optional[List[str]] = None) -> str:
    """生成模型类代码"""
    if nested_models is None:
        nested_models = []

    field_defs = []
    field_docs = []
    enum_defs = []

    for field in fields:
        if not isinstance(field, dict):
            continue

        field_name = field.get('name', '')
        field_type = field.get('type', 'str').lower()
        field_desc = field.get('description', '')
        required = field.get('required', False)
        enum_values = field.get('enum', [])

        # 处理枚举类型
        if enum_values and isinstance(enum_values, list):
            enum_name = f"{model_name}{field_name.capitalize()}Enum"
            enum_def = f'''class {enum_name}(str):
    """
    {field_desc}
    """
'''
            for value in enum_values:
                enum_value = str(value).upper().replace(' ', '_').replace('-', '_')
                enum_def += f'    {enum_value} = "{value}"\n'

            enum_defs.append(enum_def)
            field_type = enum_name

        # 处理嵌套对象
        elif field_type == 'object' and 'properties' in field:
            nested_model_name = f"{model_name}{field_name.capitalize()}"
            model_classes.add(nested_model_name)
            nested_code = generate_model_class(nested_model_name, field['properties'], model_classes, nested_models)
            nested_models.append(nested_code)
            field_type = nested_model_name

        # 处理数组类型
        elif field_type == 'array' and 'items' in field:
            items = field['items']
            if isinstance(items, dict):
                if items.get('type') == 'object' and 'properties' in items:
                    nested_model_name = f"{model_name}{field_name.capitalize()}Item"
                    model_classes.add(nested_model_name)
                    nested_code = generate_model_class(nested_model_name, items['properties'], model_classes, nested_models)
                    nested_models.append(nested_code)
                    field_type = f"List[{nested_model_name}]"
                else:
                    item_type = items.get('type', 'Any')
                    field_type = f"List[{item_type}]"
            else:
                field_type = "List[Any]"

        # 处理复合类型（如 integer/string）
        else:
            if '/' in field_type:
                sub_types = []
                for t in field_type.split('/'):
                    t = t.strip()
                    if t == 'string':
                        sub_types.append('str')
                    elif t == 'integer':
                        sub_types.append('int')
                    elif t == 'boolean':
                        sub_types.append('bool')
                    elif t == 'datetime':
                        sub_types.append('datetime')
                    elif t == 'date':
                        sub_types.append('date')
                    elif t == 'float':
                        sub_types.append('float')
                    elif t == '':
                        sub_types.append('str')
                    elif t == 'array':
                        sub_types.append('List[Any]')
                    else:
                        sub_types.append(t)
                field_type = f"Union[{', '.join(sub_types)}]"
            else:
                field_type = 'str' if field_type == 'string' else field_type
                field_type = 'int' if field_type == 'integer' else field_type
                field_type = 'bool' if field_type == 'boolean' else field_type
                field_type = 'datetime' if field_type == 'datetime' else field_type
                field_type = 'date' if field_type == 'date' else field_type
                field_type = 'float' if field_type == 'float' else field_type
                field_type = 'str' if field_type == '' else field_type
                field_type = 'List[Any]' if field_type == 'array' else field_type

        # 添加字段定义
        if required:
            field_defs.append(f"    {field_name}: {field_type}")
        else:
            field_defs.append(f"    {field_name}: Optional[{field_type}] = None")

        # 添加字段文档
        field_docs.append(f"        {field_name}: {field_desc}")

    # 生成当前模型代码
    model_code = f'''"""
Generated model class for {model_name}
"""
from typing import List, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
from .base import ZentaoModel

{chr(10).join(enum_defs)}

class {model_name}(ZentaoModel):
    """{model_name} 模型
    
    Attributes:
{chr(10).join(field_docs)}
    """
{chr(10).join(field_defs)}
'''

    # 拼接所有嵌套模型代码 + 当前模型代码
    full_code = ''
    for nested in nested_models:
        full_code += nested + '\n\n'
    full_code += model_code

    return full_code

def main():
    project_root = Path(__file__).parent.parent
    api_docs_file = project_root / "api_docs" / "zentao_api_docs.json"
    sdk_dir = project_root / "zentao_api"
    core_dir = sdk_dir / "core"
    api_dir = core_dir / "api"
    models_dir = core_dir / "models"

    sdk_dir.mkdir(exist_ok=True)
    core_dir.mkdir(exist_ok=True)
    api_dir.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)

    with open(api_docs_file, 'r', encoding='utf-8') as f:
        api_docs = json.load(f)

    # 生成基础文件
    generate_base_files(core_dir)

    # 生成模型文件
    model_classes = set()
    for group_name, methods in api_docs.get('groups', {}).items():
        for method in methods:
            if 'response_params' in method:
                response_params = method['response_params']
                if isinstance(response_params, list):
                    nested_models = []
                    model_name = f"{method['path'].strip('/').replace('/', '_').capitalize()}Response"
                    model_classes.add(model_name)
                    model_code = generate_model_class(model_name, response_params, model_classes, nested_models)
                    with open(models_dir / f"{model_name.lower()}.py", 'w', encoding='utf-8') as f:
                        f.write(model_code)

    # 生成 __init__.py
    with open(models_dir / "__init__.py", 'w', encoding='utf-8') as f:
        f.write('"""\nGenerated models for ZenTao API\n"""\n')
        f.write('from typing import List, Optional, Any\n')
        f.write('from datetime import datetime, date\n')
        f.write('from .base import ZentaoModel\n\n')
        f.write('__all__ = []\n')
        for model_class in sorted(model_classes):
            f.write(f'from .{model_class.lower()} import {model_class}\n')
        f.write('\n__all__ = [\n')
        for model_class in sorted(model_classes):
            f.write(f"    '{model_class}',\n")
        f.write(']\n')

    # 生成 API 类文件
    for group_name, methods in api_docs.get('groups', {}).items():
        if group_name:
            api_code = generate_api_class(group_name, methods, model_classes)
            with open(api_dir / f"{group_name.lower()}.py", 'w', encoding='utf-8') as f:
                f.write(api_code)

    # 生成 API __init__.py
    with open(api_dir / "__init__.py", 'w', encoding='utf-8') as f:
        f.write('"""\nGenerated API classes for ZenTao API\n"""\n')
        f.write('from typing import Dict, Any, List, Optional\n')
        f.write('from ..client import ZentaoClient\n')
        f.write('from ..models import *\n')
        f.write('from .base import BaseAPI\n\n')
        for group_name in api_docs.get('groups', {}):
            if group_name:
                f.write(f'from .{group_name.lower()} import {group_name.capitalize()}API\n')
        f.write('\n__all__ = [\n')
        for group_name in api_docs.get('groups', {}):
            if group_name:
                f.write(f"    '{group_name.capitalize()}API',\n")
        f.write(']\n')

def generate_base_files(core_dir: Path) -> None:
    """生成基础文件"""
    # 生成 base.py
    base_file = core_dir / "api" / "base.py"
    with open(base_file, 'w', encoding='utf-8') as f:
        f.write('''"""
Generated base API class for ZenTao API
"""
from typing import Dict, Any, List, Optional
from ..client import ZentaoClient

class BaseAPI:
    """ZenTao API 基类"""
    
    def __init__(self, client: ZentaoClient):
        """初始化 API 类
        
        Args:
            client: ZentaoClient 实例
        """
        self.client = client
    
    async def _request(
        self,
        method: str,
        path: str,
        path_params: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None,
        body: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            path: API 路径
            path_params: 路径参数
            query_params: 查询参数
            body: 请求体
            
        Returns:
            Dict[str, Any]: API 响应数据
        """
        return await self.client._request(
            method=method,
            path=path,
            path_params=path_params,
            query_params=query_params,
            body=body
        )
''')

    # 生成 models/base.py
    base_model_file = core_dir / "models" / "base.py"
    with open(base_model_file, 'w', encoding='utf-8') as f:
        f.write('''"""
Generated base model class for ZenTao API
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass, field

@dataclass
class ZentaoModel:
    """ZenTao API 模型基类"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典数据
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZentaoModel':
        """从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            ZentaoModel: 模型实例
        """
        return cls(**data)
''')

    # 生成 models/response.py
    response_file = core_dir / "models" / "response.py"
    with open(response_file, 'w', encoding='utf-8') as f:
        f.write('''"""
Generated response model class for ZenTao API
"""
from typing import Dict, Any, List, Optional
from .base import ZentaoModel

class Response(ZentaoModel):
    """ZenTao API 响应基类"""
    
    def __init__(self, **kwargs):
        """初始化响应类
        
        Args:
            **kwargs: 响应数据
        """
        super().__init__(**kwargs)
''')

def generate_api_class(api_name: str, api_methods: List[Dict[str, Any]], model_classes: Set[str]) -> str:
    """生成 API 类代码"""
    class_name = f"{api_name.capitalize()}API"

    class_code = f'''"""
Generated API class for {api_name}
"""
from typing import Dict, Any, List, Optional
from ..client import ZentaoClient
from ..models import *
from .base import BaseAPI

class {class_name}(BaseAPI):
    """{api_name} API 类"""
    
    def __init__(self, client: ZentaoClient):
        """初始化 {api_name} API
        
        Args:
            client: ZentaoClient 实例
        """
        super().__init__(client)

'''

    # 生成方法代码
    for method_info in api_methods:
        method_code = generate_api_method(method_info)
        class_code += method_code

    return class_code

def generate_api_method(method_info: Dict[str, Any]) -> str:
    """生成 API 方法代码"""
    method = method_info.get('method', '')
    path = method_info.get('path', '')
    description = method_info.get('description', '')
    request_params = method_info.get('request_params', [])

    # 生成方法名
    method_name = path.strip('/').split('/')[-1]
    if method_name == 'id':
        parts = path.strip('/').split('/')
        if len(parts) > 2:
            method_name = f"{parts[-2]}_{method_name}"
        if method.lower() == 'get':
            method_name = f"get_{method_name}"
        elif method.lower() == 'post':
            method_name = f"create_{method_name}"
        elif method.lower() == 'put':
            method_name = f"update_{method_name}"
        elif method.lower() == 'delete':
            method_name = f"delete_{method_name}"

    response_class = f"{path.strip('/').replace('/', '_').capitalize()}Response"

    params = []
    path_params = []
    query_params = []
    body_params = []

    for param in request_params:
        param_name = param.get('name', '')
        param_type = param.get('type', '').lower()
        required = param.get('required', False)
        description = param.get('description', '')

        if param_name == 'Token':
            continue

        if param_type == 'string':
            param_type = 'str'
        elif param_type == 'integer':
            param_type = 'int'
        elif param_type == 'boolean':
            param_type = 'bool'
        elif param_type == 'array':
            param_type = 'List[Any]'
        elif param_type == '':
            param_type = 'Any'

        if not required:
            param_type = f'Optional[{param_type}]'
            default_value = ' = None'
        else:
            default_value = ''

        params.append(f"{param_name}: {param_type}{default_value}")

        if '{' + param_name + '}' in path:
            path_params.append(param_name)
        elif method.upper() in ['GET', 'DELETE']:
            query_params.append(param_name)
        else:
            body_params.append(param_name)

    if 'id' in path and '{id}' not in path:
        path = path.replace('/id', '/{id}')
        params.append('id: int')
        path_params.append('id')

    method_code = f'''    async def {method_name}(self, {", ".join(params)}) -> {response_class}:
        """{description}
        
        Args:
'''
    for param in request_params:
        param_name = param.get('name', '')
        param_desc = param.get('description', '')
        if param_name != 'Token':
            method_code += f'            {param_name}: {param_desc}\n'

    if 'id' in path and '{id}' in path and 'id: int' in params:
        method_code += '            id: 记录 ID\n'

    method_code += f'''        
        Returns:
            {response_class}: API 响应数据
        """
        path_params = {{
'''
    for param in path_params:
        method_code += f'            "{param}": {param},\n'

    method_code += '''        }
        query_params = {
'''
    for param in query_params:
        method_code += f'            "{param}": {param} if {param} is not None else None,\n'

    method_code += '''        }
        body = {
'''
    for param in body_params:
        method_code += f'            "{param}": {param} if {param} is not None else None,\n'

    method_code += f'''        }}
        response = await self._request(
            method="{method}",
            path="{path}",
            path_params=path_params,
            query_params=query_params,
            body=body
        )
        return {response_class}(**response) if isinstance(response, dict) else response
'''

    return method_code

if __name__ == "__main__":
    main()
