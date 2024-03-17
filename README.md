# assetfetch-blender
 An AssetFetch client for Blender


# Algorithm for creating import steps

These are the steps for creating an import plan for a specific implementation.

1. Plan how to unlock all resources in the `implementation`
	- Take the list of unlocking queries from the `unlocking_queries` datablock in the `implementation_list`
	- For every `component` in the `implementation`, check for an `unlock_link` datablock. If present, add the referenced unlocking query to a list of required queries, if it isn't already on it.
	- At this point, it is clear which unlocking queries will be required to call when/if this import plan is executed.
2. Plan how to assemble the local asset directory.
	- With every `component`, one of the scenarios in the table can occur. The table's columns represent the possible values for `behavior` in the `file_info` datablock. The table's rows represent the possible fetching-related datablocks present on the `component`.

|                                         | `file_active` or `file_passive`, both with `local_path`                                | `archive` with `local_path`                                                                                       | `archive` without `local_path`                                          |
| --------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Has `file_fetch.download` datablock     | Download directly into the `local_path` using the provided query.                      | Download and extract into temp. directory, then copy full contents into `local_path`                              | Download and extract into temp. directory.                              |
| Has `file_fetch.from_archive` datablock | Handle referenced archive component. Then copy from temp. directory into `local_path`. | Handle referenced archive component, then extract into temp. directory, then copy full contents into `local_path` | Handle referenced archive component, then extract into temp. directory. |
| Has `unlock_link` datablock             | Fetch and handle the `file_fetch.download` datablock from the response.                | Fetch and handle the `file_fetch.download` datablock from the response.                                           | Fetch and handle the `file_fetch.download` datablock from the response. |

3. Plan how to import all active files.
	- If files have no `loose_material` or `loose_environment` datablocks: Delegate import to native handler.
	- 