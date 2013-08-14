# SECRETARY

#### Take the power of Jinja2 templates to OpenOffice and LibreOffice and create reports in your web applications.


**Secretary** allows you to use Open Document Text (ODT) files as templates for rendering reports or letters. Secretary is an alternative solution for creating office documents and reports in OpenDocument Text format from templates that can be visually composed using the OpenOffice.org/LibreOffice Writer word processor.

Secretary use [the semantics of jinja2 templates][1] to render ODT files. Most features in jinja can be used into your ODT templates including variable printing, filters and flow control.

Rendered documents are produced in ODT format, and can then be converted to PDF, MS Word or other supported formats using the UNO Bridge or a library like [PyODConverter][2]

## Rendering a Template

    from secreatary import Render
    
    engine = Render(template)
    result = engine.render(foo=foo, bar=bar)

Secretary implements a class called `Render`. `Render` takes a single argument called `template` which is a template file. `template` can be a filename or a file object.

To render a template create an instance of class `Render` and call the instance's method `render` passing the template variables as keyword arguments. `render` will return the rendered document in binary format.

Before rendering a template, you can configure the internal templating engine using the `Render` instance's variable `environment`, which is an instance of jinja2 **[Environment][3]** class. For example, to declare a custom filter use:

    from secreatary import Render
    
    engine = Render(template)

    # Configure custom application filters
    engine.environment.filters['custom_filer'] = filter_function
    result = engine.render(foo=foo, bar=bar)

    output = open('rendered_document.odt', 'w')
    output.write(result)

## Composing Templates

Secretary templates are simple ODT documents. You can create them using Writer. An OpenDocument file is basically a ZIP archive containing some XML files. If you plan to use control flow or conditionals it is a good idea to familiarise yourself a little bit with the OpenDocument XML to understand better what's going on behind the scenes.

### Printing Variables

Since Secretary use the same template syntax of Jinja2, to print a varible type a double curly braces enclosing the variable, like so:

    {{ foo.bar }}
    {{ foo['bar'] }}

However, mixing template instructions and normal text into the template document may become confusing and clutter the layout. Secretary recommends using an alternative way of inserting fields. Insert a visual field in LibreOffice Writer from the menu `Insert` > `Fields` > `Other...` (or just press `Ctrl+F2`), then click on the `Functions` tab and select `Input field`. Click `Insert`. A dialog will appear where you can insert the print instructions. You can even insert simple control flow tags to dynamically change what is printed in the field.

Secretary will handle multiline variable values replacing the line breaks with a `<text:line-break/>` tag.

### Control Flow

To be documented... 


  [1]: http://jinja.pocoo.org/docs/templates/
  [2]: https://github.com/mirkonasato/pyodconverter
  [3]: http://jinja.pocoo.org/docs/api/#jinja2.Environment
