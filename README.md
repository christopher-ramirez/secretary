# SECRETARY


<a href="https://pypi.python.org/pypi/secretary">
<img src="https://img.shields.io/pypi/v/secretary.svg" />
</a>
<a href="https://travis-ci.org/christopher-ramirez/secretary">
<img src="https://img.shields.io/travis/christopher-ramirez/secretary.svg" />
</a>

#### Take the power of Jinja2 templates to OpenOffice and LibreOffice and create reports in your web applications.


**Secretary** allows you to use Open Document Text (ODT) files as templates for rendering reports or letters. Secretary is an alternative solution for creating office documents and reports in OpenDocument Text format from templates that can be visually composed using the OpenOffice.org/LibreOffice Writer word processor.

Secretary use [the semantics of jinja2 templates][1] to render ODT files. Most features in jinja can be used into your ODT templates including variable printing, filters and flow control.

Rendered documents are produced in ODT format, and can then be converted to PDF, MS Word or other supported formats using the UNO Bridge or a library like [PyODConverter][2]

## Installing

    pip install secretary

## Rendering a Template
```python
    from secretary import Renderer

    engine = Renderer()
    result = engine.render(template, foo=foo, bar=bar)
```

Secretary implements a class called `Renderer`. `Renderer` takes a single argument called `environment` which is a jinja **[Environment][3]**.

To render a template create an instance of class `Renderer` and call the instance's method `render` passing a template file and template's variables as keyword arguments. `template` can be a filename or a file object. `render` will return the rendered document in binary format.

Before rendering a template, you can configure the internal templating engine using the `Renderer` instance's variable `environment`, which is an instance of jinja2 **[Environment][3]** class. For example, to declare a custom filter use:
```python
    from secretary import Renderer

    engine = Renderer()

    # Configure custom application filters
    engine.environment.filters['custom_filer'] = filter_function
    result = engine.render(template, foo=foo, bar=bar)

    output = open('rendered_document.odt', 'wb')
    output.write(result)
```

## Composing Templates

Secretary templates are simple ODT documents. You can create them using Writer. An OpenDocument file is basically a ZIP archive containing some XML files. If you plan to use control flow or conditionals it is a good idea to familiarise yourself a little bit with the OpenDocument XML to understand better what's going on behind the scenes.

### Printing Variables

Since Secretary use the same template syntax of Jinja2, to print a varible type a double curly braces enclosing the variable, like so:
```jinja
    {{ foo.bar }}
    {{ foo['bar'] }}
```

However, mixing template instructions and normal text into the template document may become confusing and clutter the layout and most important, in most cases will produce invalid ODT documents. Secretary recommends using an alternative way of inserting fields. Insert a visual field in LibreOffice Writer from the menu `Insert` > `Fields` > `Other...` (or just press `Ctrl+F2`), then click on the `Functions` tab and select `Input field`. Click `Insert`. A dialog will appear where you can insert the print instructions. You can even insert simple control flow tags to dynamically change what is printed in the field.

Secretary will handle multiline variable values replacing the line breaks with a `<text:line-break/>` tag.

### Control Flow

Most of the time secretary will handle the internal composing of XML when you insert control flow tags (`{% for foo in foos %}`, `{% if bar %}`, etc and its enclosing tags. This is done by finding the present or absence of other secretary tags within the internal XML tree.

#### Examples document structures
**Printing multiple records in a table**
![alt tag](https://github.com/christopher-ramirez/secretary/blob/development/docs/images/table_01.png)

**Conditional paragraphs**
![alt tag](https://github.com/christopher-ramirez/secretary/blob/development/docs/images/conditional_paragraph_01.png)

The last example could had been simplified into a single paragraph in Writer like:
```jinja
    {% if already_paid %}YOU ALREADY PAID{% else %}YOU HAVEN'T PAID{% endif %}
```

**Printing a list of names**
```jinja
    {% for name in names %}
        {{ name }}
    {% endfor %}
```

Automatic control flow in Secretary will handle the intuitive result of the above examples and similar thereof.

Although most of the time the automatic handling of control flow in secretary may be good enough, we still provide an additional method for manual control of the flow. Use the `reference` property of the field to specify where where the control flow tag will be used or internally moved within the XML document:

* `paragraph`: Whole paragraph containing the field will be replaced with the field content.
* `before::paragraph`: Field content will be moved before the current paragraph.
* `after::paragraph`: Field content will be moved after the current paragraph.
* `row`: The entire table row containing the field will be replace with the field content.
* `before::row`: Field content will be moved before the current table row.
* `after::row`: Field content will be moved after the current table row.
* `cell`: The entire table cell will be replaced with the current field content. Even though this setting is available, it is not recommended. Generated documents may not be what you expected.
* `before::cell`: Same as `before::row` but for a table cell.
* `after::cell`: Same as `after::row` but for a table cell.
> Field content is the control flow tag you insert with the Writer *input field*

### Hyperlink  Support
LibreOffice by default escapes every URL in links, pictures or any other element supporting hyperlink functionallity. This can be a problem if you need to generate dynamic links because your template logic is URL encoded and impossible to be handled by the Jinja engine. Secretary solves this problem by reserving the `secretary` URI scheme. If you need to create dynamic links in your documents, prepend every link with the `secretary:` scheme.

So for example if you have the following dynamic link: `https://mysite/products/{{ product.id }}`, prepend it with the **`secretary:`** scheme, leaving the final link as `secretary:https://mysite/products/{{ product.id }}`.

### Image Support
Secretary allows you to use placeholder images in templates that will be replaced when rendering the final document. To create a placeholder image on your template:

1. Insert an image into the document as normal. This image will be replaced when rendering the final document.
2. Change the name of the recently added image to a Jinja2 print tag (the ones with double curly braces). The variable should call the `image` filter, i.e.: Suppose you have a client record (passed to template as `client` object), and a picture of him is stored in the `picture` field. To print the client's picture into a document set the image name to `{{ client.picture|image }}`.

> To change image name, right click under image, select "Picture..." from the popup menu and navigate to
"Options" tab.

#### Media loader
To load image data, Secretary needs a media loader. The engine by default provides a file system loader which takes the variable value (specified in image name). This value can be a file object containing an image or an absolute or a relative filename to `media_path` passed at `Renderer` instance creation.

Since the default media loader is very limited. Users can provide theirs own media loader to the `Renderer` instance. A media loader can perform image retrieval and/or any required transformation of images. The media loader must take the image value from the template and return a tuple whose first item is a file object containing the image. Its second element must be the image mimetype.

Example declaring a media loader:
```python
    from secretary import Renderer

    engine = Renderer()

    @engine.media_loader
    def db_images_loader(value, *args, *kwargs):
        # load from images collection the image with `value` id.
        image = db.images.findOne({'_id': value})

        return (image, the_image_mimetype)

    engine.render(template, **template_vars)
```
The media loader also receive any argument or keywork arguments declared in the template. i.e: If the placeholder image's name is: `{{ client.image|image('keep_ratio', tiny=True)}}` the media loader will receive: first the value of `client.image` as it first argument; the string `keep_ratio` as an additional argument and `tiny` as a keyword argument.

The loader can also access and update the internal `draw:frame` and `draw:image` nodes. The loader receives as a dictionary the attributes of these nodes through `frame_attrs` and `image_attrs` keyword arguments. Is some update is made to these dictionary secretary will update the internal nodes with the changes. This is useful when the placeholder's aspect radio and replacement image's aspect radio are different and you need to keep the aspect ratio of the original image.

### Builtin Filters
Secretary includes some predefined *jinja2* filters. Included filters are:

- **image(value)**
See *Image Support* section above.

- **markdown(value)**
Convert the value, a markdown formated string, into a ODT formated text. Example:

        {{ invoice.description|markdown }}

- **pad(value, length)**
Pad zeroes to `value` to the left until output value's length be equal to `length`. Default length if 5. Example:

        {{ invoice.number|pad(6) }}

### Features of jinja2 not supported
Secretary supports most of the jinja2 control structure/flow tags. But please avoid using the following tags since they are not supported: `block`, `extends`, `macro`, `call`, `include` and `import`.

### Version History
* **0.2.18**:
    1. Auto escaping of Secretary URL scheme was not working on Python 3.
    2. Is not longer needed to manually set as safe the output value of the markdown filter.
* **0.2.17**: Performance increase when escaping `\n` and `\t` chars. See [#44](https://github.com/christopher-ramirez/secretary/issues/44).
* **0.2.16**: Fix store of mimetype in rendered ODT archive.
* **0.2.15**: Fix bug reported in #39 escaping Line-Feed and Tab chars inside `text:` elements.
* **0.2.14**: Implement dynamic links escaping and fix #33.
* **0.2.13**: Fix reported bug in markdown filter outputing emply lists.
* **0.2.11**: Fix bug when unescaping `&quot;`, `&apos;`, `&lt;`, `&gt;` and '&amp;' inside Jinja expressions.
* **0.2.10**: ---
* **0.2.9**: ---
* **0.2.8**: Fix #25. Some internal refactorings. Drop the minimal support for Jinja tags in plain text.
* **0.2.7**: Truly fix regexps used to unscape XML entities present inside Jinja tags.
* **0.2.6**: **AVOID THIS RELEASE** ~~Fix regexps used to unscape XML entities present inside Jinja tags.~~
* **0.2.5**: Fix issues [#14](https://github.com/christopher-ramirez/secretary/issues/14) and [#16](https://github.com/christopher-ramirez/secretary/issues/16). Thanks to [DieterBuysAI](/DieterBuysAI) for this release.
* **0.2.4**: Fix an UnicodeEncodeError exception raised scaping tab chars.
* **0.2.3**: Fix issue [#12](https://github.com/christopher-ramirez/secretary/issues/12).
* **0.2.2**: Introduce image support.
* **0.2.1**: Fix issue [#8](https://github.com/christopher-ramirez/secretary/issues/8)
* **0.2.0**: **Backward incompatible release**. Still compatible with existing templates. Introduce auto flow handling, better logging and minor bug fixes.
* **0.1.1**: New markdown filter. Introduce new flow control aliases. Bug fixes.
* **0.1.0**: Initial release.


  [1]: http://jinja.pocoo.org/docs/templates/
  [2]: https://github.com/mirkonasato/pyodconverter
  [3]: http://jinja.pocoo.org/docs/api/#jinja2.Environment
