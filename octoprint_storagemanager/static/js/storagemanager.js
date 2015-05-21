$(function () {
    function StorageManagerViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];

        self.file_path = ko.observable(undefined);

        self.searchQuery = ko.observable(undefined);
        self.searchQuery.subscribe(function () {
            self.performSearch();
        });

        // initialize list helper
        self.listHelper1 = new ItemListHelper(
            "files",
            {
                "name": function (a, b) {
                    // sorts ascending
                    if (a["name"].toLocaleLowerCase() < b["name"].toLocaleLowerCase()) return -1;
                    if (a["name"].toLocaleLowerCase() > b["name"].toLocaleLowerCase()) return 1;
                    return 0;
                },
            },
            {
            },
            "name",
            [],
            [],
            10
        );
        self.listHelper2 = new ItemListHelper(
            "files",
            {
                "name": function (a, b) {
                    // sorts ascending
                    if (a["name"].toLocaleLowerCase() < b["name"].toLocaleLowerCase()) return -1;
                    if (a["name"].toLocaleLowerCase() > b["name"].toLocaleLowerCase()) return 1;
                    return 0;
                },
            },
            {
            },
            "name",
            [],
            [],
            10
        );

        self.upload_button = $("#settings-upload-start");
        self.upload_file = $("#settings-upload");
        self.files_url = $("#settings-files").data().url;

        self.upload_file.fileupload({
            dataType: "json",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function (e, data) {
                if (data.files.length == 0) {
                    return false;
                }
                self.file_path(data.files[0].name);
                self.upload_button.unbind("click");
                self.upload_button.on("click", function () {
                    data.submit();
                });
            },
            done: function (e, data) {
                self.requestData();
                return;
            }
        });

        self.requestData = function () {
            $.ajax({
                url: self.files_url,
                type: "GET",
                dataType: "json",
                success: self.fromResponse
            });
        };

        self.fromResponse = function (response) {
            var files = response.files;
            if (files === undefined)
                return;

            self.listHelper1.updateItems(files);
            self.listHelper2.updateItems(files);
        };

        self.removeFile = function (filename) {
            $.ajax({
                url: self.files_url + "/" + filename,
                type: "DELETE",
                dataType: "json",
                success: self.requestData
            });
        };

        self.performSearch = function () {
            var query = self.searchQuery();
            if (query !== undefined && query.trim() != "") {
                self.listHelper2.changeSearchFunction(function (entry) {
                    return entry && entry["name"].toLocaleLowerCase().indexOf(query) > -1;
                });
            } else {
                self.listHelper2.resetSearch();
            }
        };

        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
        };

        self.onUserLoggedIn = function (user) {
            self.requestData();
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        StorageManagerViewModel,
        ["settingsViewModel", "loginStateViewModel"],
        ["#settings_plugin_storagemanager", "#sidebar_plugin_storagemanager"]
    ]);
});