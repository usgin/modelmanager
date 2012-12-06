// From https://gist.github.com/868595

dojo.require("dijit.Editor");

// extra plugins
dojo.require("dojox.editor.plugins.Blockquote");
dojo.require("dijit._editor.plugins.LinkDialog");
dojo.require("dojox.editor.plugins.ShowBlockNodes");
dojo.require("dojox.editor.plugins.PasteFromWord");
dojo.require("dojox.editor.plugins.InsertEntity");
dojo.require("dijit._editor.plugins.ViewSource");

// headless plugins
dojo.require("dojox.editor.plugins.NormalizeIndentOutdent");
dojo.require("dojox.editor.plugins.PrettyPrint");	// let's pretty-print our HTML
dojo.require("dojox.editor.plugins.AutoUrlLink");
dojo.require("dojox.editor.plugins.ToolbarLineBreak");

dojo.ready(function(){
  var textareas = dojo.query("textarea");
  if(textareas && textareas.length){
    dojo.addClass(dojo.body(), "claro");
    textareas.instantiate(dijit.Editor, {
      plugins: [
        "undo", "redo", "|",
        "cut", "copy", "paste", "pastefromword", "|",
        "bold", "italic", "underline", "strikethrough", "|",
        "insertOrderedList", "insertUnorderedList", "indent", "outdent", "|",
        "createLink",
        "normalizeindentoutdent", "prettyprint",
        "autourllink", "dijit._editor.plugins.EnterKeyHandling",
        "viewsource"
      ]
    });
  }
});