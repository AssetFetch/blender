import bpy
from typing import List,Dict
from .http_handler import *

class ImplementationValidationResult():
	ok : bool = True
	comments: List[str] = []

	def __str__(self) -> str:
		return json.dumps({"ok":self.ok,"comments":self.comments})
		pass


def validate_implementation(implementation) -> ImplementationValidationResult:
	components = implementation['components']
	result = ImplementationValidationResult()
	for comp in components:

		# resolve_file
		if not comp['data']['resolve_file']:
			result.ok = False
			result.comments.append(f"{comp['id']} is missing a 'resolve_file' datablock.")
			continue
		
		if comp['data']['resolve_file']['extension'] not in ('.obj','.jpg'):
			result.ok = False
			result.comments.append(f"{comp['id']} is using the extension '{comp['data']['resolve_file']['extension']}' which is unsupported.")

	return result


class AF_Import_Plan_Task:
	def execute():
		pass

class AF_Import_Plan_Task_Download(AF_Import_Plan_Task):
	query : AF_HttpQuery
	local_path : str
	def execute():
		pass

class AF_Import_Plan_Task_Import_Obj(AF_Import_Plan_Task):
	local_path: str
	upaxis: str

	def execute():
		pass

class AF_Import_Plan_Task_Import_Image(AF_Import_Plan_Task):
	local_path: str
	material: str
	
	def execute():
		pass

class AF_Import_Plan_Task_Create_Material(AF_Import_Plan_Task):
	name: str

	def execute():
		pass

class AF_Import_Plan_Task_Assign_Material(AF_Import_Plan_Task):
	material: any
	target_object: any

	def execute():
		pass

class AF_Import_Plan:
	tasks: List[AF_Import_Plan_Task] = []
	created_objects: List[any]