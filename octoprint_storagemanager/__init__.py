# coding=utf-8
from __future__ import absolute_import

from flask import request, jsonify, make_response, url_for, send_from_directory
from werkzeug.utils import secure_filename

import octoprint.filemanager.util
import octoprint.plugin
import octoprint.settings
from octoprint.server import NO_CONTENT, admin_permission, user_permission
from octoprint.server.util.flask import restricted_access
import os

class StorageManagerPlugin(octoprint.plugin.TemplatePlugin,
						   octoprint.plugin.SettingsPlugin,
						   octoprint.plugin.AssetPlugin,
						   octoprint.plugin.BlueprintPlugin):
	
	##~~ AssetsPlugin
	def get_assets(self):
		return dict(
			js=["js/storagemanager.js"],
			css=["css/storagemanager.css"]
		)

	##~~ Set default settings
	def get_settings_defaults(self):
		return dict(storage_path=None)


	def get_template_configs(self):
		return [
			dict(type="sidebar", get_template_configs="storagemanager_sidebar.jinja2", data_bind="visible: loginState.isUser")
		]

	##~~ BlueprintPlugin API

	def is_blueprint_protected(self):
		return False

	@octoprint.plugin.BlueprintPlugin.route("/upload", methods=["POST"])
	@restricted_access
	@admin_permission.require(403)
	def uploadFile(self):
		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		if input_upload_name in request.values and input_upload_path in request.values:
			upload = octoprint.filemanager.util.DiskFileWrapper(request.values[input_upload_name], request.values[input_upload_path])
		else:
			self._logger.warn("Nothing included for uploading, aborting")
			return make_response("No file included", 400)

		path = self._settings.get(["storage_path"])
		if path is None:
			return make_response("No storage path configured!", 500)
		
		# make sure folders exist
		if not os.path.exists(path):
			os.makedirs(path)

		file_path = os.path.join(path, upload.filename)
		if os.path.exists(file_path) and not os.path.isfile(file_path):
			raise RuntimeError("{name} does already exist in {path} and is not a file".format(**locals()))

		upload.save(file_path)

		return NO_CONTENT

	@octoprint.plugin.BlueprintPlugin.route("/files", methods=["GET"])
	@restricted_access
	@user_permission.require(403)
	def listFiles(self):
		path = self._settings.get(["storage_path"])
		if path is None:
			return jsonify(files=dict())

		files = self._list_folder(path)
		return jsonify(files=files)

	@octoprint.plugin.BlueprintPlugin.route("/files/<path:filename>", methods=["DELETE"])
	@restricted_access
	@admin_permission.require(403)
	def deleteFiles(self, filename):
		path = self._settings.get(["storage_path"])
		if path is None:
			return jsonify(files=dict())

		secure = os.path.join(path, secure_filename(filename))
		if not os.path.exists(secure):
			return make_response("File not found: %s" % filename, 404)

		os.remove(secure)
		return NO_CONTENT

	@octoprint.plugin.BlueprintPlugin.route("/download/<path:filename>")
	@restricted_access
	@user_permission.require(403)
	def download(self, filename):
		path = self._settings.get(["storage_path"])
		if path is None:
			return jsonify(files=dict())

		secure = os.path.join(path, secure_filename(filename))
		if not os.path.exists(secure):
			return make_response("File not found: %s" % filename, 404)

		return send_from_directory(path, secure_filename(filename), as_attachment=True)

	def _list_folder(self, path, recursive=True):
		result = []
		for entry in os.listdir(path):
			if entry.startswith("."):
				# no hidden files and folders
				continue

			entry_path = os.path.join(path, entry)

			# file handling
			if os.path.isfile(entry_path):
				result.append(dict(
					name=entry,
					type="file",
					refs=dict(
						download=url_for("plugin.storagemanager.download", filename=entry)
					)
				))

			# folder recursion
			elif os.path.isdir(entry_path) and recursive:
				sub_result = self._list_folder(entry_path)
				result.append(dict(
					name=entry,
					type="folder",
					children=sub_result,
				))

		return result

__plugin_name__ = "Storage Manager"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = StorageManagerPlugin()

	# global __plugin_hooks__
	# __plugin_hooks__ = {"some.octoprint.hook": __plugin_implementation__.some_hook_handler}
