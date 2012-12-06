$(document).ready(function() {
  var versionArray = {};
  var cmSelect = $("#id_content_model");
  var vSelect = $("#id_version");
  
  // Get all the available versions in an array with the ContentModel name as key
  // Loop through ContentModels, add keys to the array
  cmSelect.children("option").each(function() {
    versionArray[$(this).text()] = [];
  });
  
  // Loop through the Versions
  vSelect.children("option").each(function() {
    var vModel = $(this).text().split(" v. ")[0];
    versionArray[vModel].push($(this));
  });
  
  // Define a function to set the Version picklist to only a given model
  function defineVersions(event) {
    var modelName = cmSelect.children("option").filter(":selected").text();
    vSelect.empty();
    var versions = versionArray[modelName];
    for (var i = 0; i < versions.length; i++) {
      vSelect.append(versions[i]);
    }
  };
  
  // Bind that function to the ContentModel select's change event
  cmSelect.change(defineVersions);
  
  // Empty the version select for now...
  vSelect.empty();
});

