from typing import Dict,List

def dict_to_attr(source:Dict[str,str],keys:List[str],destination:any):
	for key in keys:
		if key in source:
			setattr(destination,key,source[key])