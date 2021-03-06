# coding: utf-8

"""
Unit tests of template.py.

"""

import codecs
import os
import sys
import unittest

from examples.simple import Simple
from pystache_custom import Renderer
from pystache_custom import TemplateSpec
from pystache_custom.common import TemplateNotFoundError
from pystache_custom.loader import Loader

from pystache_custom.tests.common import get_data_path, AssertStringMixin, AssertExceptionMixin
from pystache_custom.tests.data.views import SayHello


def _make_renderer():
    """
    Return a default Renderer instance for testing purposes.

    """
    renderer = Renderer(string_encoding='ascii', file_encoding='ascii')
    return renderer


def mock_unicode(b, encoding=None):
    if encoding is None:
        encoding = 'ascii'
    u = unicode(b, encoding=encoding)
    return u.upper()


class RendererInitTestCase(unittest.TestCase):

    """
    Tests the Renderer.__init__() method.

    """

    def test_partials__default(self):
        """
        Test the default value.

        """
        renderer = Renderer()
        self.assertTrue(renderer.partials is None)

    def test_partials(self):
        """
        Test that the attribute is set correctly.

        """
        renderer = Renderer(partials={'foo': 'bar'})
        self.assertEqual(renderer.partials, {'foo': 'bar'})

    def test_escape__default(self):
        escape = Renderer().escape

        self.assertEqual(escape(">"), "&gt;")
        self.assertEqual(escape('"'), "&quot;")
        # Single quotes are escaped only in Python 3.2 and later.
        if sys.version_info < (3, 2):
            expected = "'"
        else:
            expected = '&#x27;'
        self.assertEqual(escape("'"), expected)

    def test_escape(self):
        escape = lambda s: "**" + s
        renderer = Renderer(escape=escape)
        self.assertEqual(renderer.escape("bar"), "**bar")

    def test_decode_errors__default(self):
        """
        Check the default value.

        """
        renderer = Renderer()
        self.assertEqual(renderer.decode_errors, 'strict')

    def test_decode_errors(self):
        """
        Check that the constructor sets the attribute correctly.

        """
        renderer = Renderer(decode_errors="foo")
        self.assertEqual(renderer.decode_errors, "foo")

    def test_file_encoding__default(self):
        """
        Check the file_encoding default.

        """
        renderer = Renderer()
        self.assertEqual(renderer.file_encoding, renderer.string_encoding)

    def test_file_encoding(self):
        """
        Check that the file_encoding attribute is set correctly.

        """
        renderer = Renderer(file_encoding='foo')
        self.assertEqual(renderer.file_encoding, 'foo')

    def test_file_extension__default(self):
        """
        Check the file_extension default.

        """
        renderer = Renderer()
        self.assertEqual(renderer.file_extension, 'mustache')

    def test_file_extension(self):
        """
        Check that the file_encoding attribute is set correctly.

        """
        renderer = Renderer(file_extension='foo')
        self.assertEqual(renderer.file_extension, 'foo')

    def test_search_dirs__default(self):
        """
        Check the search_dirs default.

        """
        renderer = Renderer()
        self.assertEqual(renderer.search_dirs, [os.curdir])

    def test_search_dirs__string(self):
        """
        Check that the search_dirs attribute is set correctly when a string.

        """
        renderer = Renderer(search_dirs='foo')
        self.assertEqual(renderer.search_dirs, ['foo'])

    def test_search_dirs__list(self):
        """
        Check that the search_dirs attribute is set correctly when a list.

        """
        renderer = Renderer(search_dirs=['foo'])
        self.assertEqual(renderer.search_dirs, ['foo'])

    def test_string_encoding__default(self):
        """
        Check the default value.

        """
        renderer = Renderer()
        self.assertEqual(renderer.string_encoding, sys.getdefaultencoding())

    def test_string_encoding(self):
        """
        Check that the constructor sets the attribute correctly.

        """
        renderer = Renderer(string_encoding="foo")
        self.assertEqual(renderer.string_encoding, "foo")


class RendererTests(unittest.TestCase, AssertStringMixin):

    """Test the Renderer class."""

    def _renderer(self):
        return Renderer()

    ## Test Renderer.unicode().

    def test_unicode__string_encoding(self):
        """
        Test that the string_encoding attribute is respected.

        """
        renderer = self._renderer()
        b = u"é".encode('utf-8')

        renderer.string_encoding = "ascii"
        self.assertRaises(UnicodeDecodeError, renderer.unicode, b)

        renderer.string_encoding = "utf-8"
        self.assertEqual(renderer.unicode(b), u"é")

    def test_unicode__decode_errors(self):
        """
        Test that the decode_errors attribute is respected.

        """
        renderer = self._renderer()
        renderer.string_encoding = "ascii"
        b = u"déf".encode('utf-8')

        renderer.decode_errors = "ignore"
        self.assertEqual(renderer.unicode(b), "df")

        renderer.decode_errors = "replace"
        # U+FFFD is the official Unicode replacement character.
        self.assertEqual(renderer.unicode(b), u'd\ufffd\ufffdf')

    ## Test the _make_loader() method.

    def test__make_loader__return_type(self):
        """
        Test that _make_loader() returns a Loader.

        """
        renderer = self._renderer()
        loader = renderer._make_loader()

        self.assertEqual(type(loader), Loader)

    def test__make_loader__attributes(self):
        """
        Test that _make_loader() sets all attributes correctly..

        """
        unicode_ = lambda x: x

        renderer = self._renderer()
        renderer.file_encoding = 'enc'
        renderer.file_extension = 'ext'
        renderer.unicode = unicode_

        loader = renderer._make_loader()

        self.assertEqual(loader.extension, 'ext')
        self.assertEqual(loader.file_encoding, 'enc')
        self.assertEqual(loader.to_unicode, unicode_)

    ## Test the render() method.

    def test_render__return_type(self):
        """
        Check that render() returns a string of type unicode.

        """
        renderer = self._renderer()
        rendered = renderer.render('foo')
        self.assertEqual(type(rendered), unicode)

    def test_render__unicode(self):
        renderer = self._renderer()
        actual = renderer.render(u'foo')
        self.assertEqual(actual, u'foo')

    def test_render__str(self):
        renderer = self._renderer()
        actual = renderer.render('foo')
        self.assertEqual(actual, 'foo')

    def test_render__non_ascii_character(self):
        renderer = self._renderer()
        actual = renderer.render(u'Poincaré')
        self.assertEqual(actual, u'Poincaré')

    def test_render__context(self):
        """
        Test render(): passing a context.

        """
        renderer = self._renderer()
        self.assertEqual(renderer.render('Hi {{person}}', {'person': 'Mom'}), 'Hi Mom')

    def test_render__context_and_kwargs(self):
        """
        Test render(): passing a context and **kwargs.

        """
        renderer = self._renderer()
        template = 'Hi {{person1}} and {{person2}}'
        self.assertEqual(renderer.render(template, {'person1': 'Mom'}, person2='Dad'), 'Hi Mom and Dad')

    def test_render__kwargs_and_no_context(self):
        """
        Test render(): passing **kwargs and no context.

        """
        renderer = self._renderer()
        self.assertEqual(renderer.render('Hi {{person}}', person='Mom'), 'Hi Mom')

    def test_render__context_and_kwargs__precedence(self):
        """
        Test render(): **kwargs takes precedence over context.

        """
        renderer = self._renderer()
        self.assertEqual(renderer.render('Hi {{person}}', {'person': 'Mom'}, person='Dad'), 'Hi Dad')

    def test_render__kwargs_does_not_modify_context(self):
        """
        Test render(): passing **kwargs does not modify the passed context.

        """
        context = {}
        renderer = self._renderer()
        renderer.render('Hi {{person}}', context=context, foo="bar")
        self.assertEqual(context, {})

    def test_render__nonascii_template(self):
        """
        Test passing a non-unicode template with non-ascii characters.

        """
        renderer = _make_renderer()
        template = u"déf".encode("utf-8")

        # Check that decode_errors and string_encoding are both respected.
        renderer.decode_errors = 'ignore'
        renderer.string_encoding = 'ascii'
        self.assertEqual(renderer.render(template), "df")

        renderer.string_encoding = 'utf_8'
        self.assertEqual(renderer.render(template), u"déf")

    def test_make_load_partial(self):
        """
        Test the _make_load_partial() method.

        """
        renderer = Renderer()
        renderer.partials = {'foo': 'bar'}
        load_partial = renderer._make_load_partial()

        actual = load_partial('foo')
        self.assertEqual(actual, 'bar')
        self.assertEqual(type(actual), unicode, "RenderEngine requires that "
            "load_partial return unicode strings.")

    def test_make_load_partial__unicode(self):
        """
        Test _make_load_partial(): that load_partial doesn't "double-decode" Unicode.

        """
        renderer = Renderer()

        renderer.partials = {'partial': 'foo'}
        load_partial = renderer._make_load_partial()
        self.assertEqual(load_partial("partial"), "foo")

        # Now with a value that is already unicode.
        renderer.partials = {'partial': u'foo'}
        load_partial = renderer._make_load_partial()
        # If the next line failed, we would get the following error:
        #   TypeError: decoding Unicode is not supported
        self.assertEqual(load_partial("partial"), "foo")

    def test_render_path(self):
        """
        Test the render_path() method.

        """
        renderer = Renderer()
        path = get_data_path('say_hello.mustache')
        actual = renderer.render_path(path, to='foo')
        self.assertEqual(actual, "Hello, foo")

    def test_render__object(self):
        """
        Test rendering an object instance.

        """
        renderer = Renderer()

        say_hello = SayHello()
        actual = renderer.render(say_hello)
        self.assertEqual('Hello, World', actual)

        actual = renderer.render(say_hello, to='Mars')
        self.assertEqual('Hello, Mars', actual)

    def test_render__template_spec(self):
        """
        Test rendering a TemplateSpec instance.

        """
        renderer = Renderer()

        class Spec(TemplateSpec):
            template = "hello, {{to}}"
            to = 'world'

        spec = Spec()
        actual = renderer.render(spec)
        self.assertString(actual, u'hello, world')

    def test_render__view(self):
        """
        Test rendering a View instance.

        """
        renderer = Renderer()

        view = Simple()
        actual = renderer.render(view)
        self.assertEqual('Hi pizza!', actual)


# By testing that Renderer.render() constructs the right RenderEngine,
# we no longer need to exercise all rendering code paths through
# the Renderer.  It suffices to test rendering paths through the
# RenderEngine for the same amount of code coverage.
class Renderer_MakeRenderEngineTests(unittest.TestCase, AssertExceptionMixin):

    """
    Check the RenderEngine returned by Renderer._make_render_engine().

    """

    def _make_renderer(self):
        """
        Return a default Renderer instance for testing purposes.

        """
        return _make_renderer()

    ## Test the engine's load_partial attribute.

    def test__load_partial__returns_unicode(self):
        """
        Check that load_partial returns unicode (and not a subclass).

        """
        class MyUnicode(unicode):
            pass

        renderer = Renderer()
        renderer.string_encoding = 'ascii'
        renderer.partials = {'str': 'foo', 'subclass': MyUnicode('abc')}

        engine = renderer._make_render_engine()

        actual = engine.load_partial('str')
        self.assertEqual(actual, "foo")
        self.assertEqual(type(actual), unicode)

        # Check that unicode subclasses are not preserved.
        actual = engine.load_partial('subclass')
        self.assertEqual(actual, "abc")
        self.assertEqual(type(actual), unicode)

    def test__load_partial__not_found__default(self):
        """
        Check that load_partial provides a nice message when a template is not found.

        """
        renderer = Renderer()

        engine = renderer._make_render_engine()
        load_partial = engine.load_partial

        self.assertException(TemplateNotFoundError, "File 'foo.mustache' not found in dirs: ['.']",
                             load_partial, "foo")

    def test__load_partial__not_found__dict(self):
        """
        Check that load_partial provides a nice message when a template is not found.

        """
        renderer = Renderer()
        renderer.partials = {}

        engine = renderer._make_render_engine()
        load_partial = engine.load_partial

        # Include dict directly since str(dict) is different in Python 2 and 3:
        #   <type 'dict'> versus <class 'dict'>, respectively.
        self.assertException(TemplateNotFoundError, "Name 'foo' not found in partials: %s" % dict,
                             load_partial, "foo")

    ## Test the engine's literal attribute.

    def test__literal__uses_renderer_unicode(self):
        """
        Test that literal uses the renderer's unicode function.

        """
        renderer = self._make_renderer()
        renderer.unicode = mock_unicode

        engine = renderer._make_render_engine()
        literal = engine.literal

        b = u"foo".encode("ascii")
        self.assertEqual(literal(b), "FOO")

    def test__literal__handles_unicode(self):
        """
        Test that literal doesn't try to "double decode" unicode.

        """
        renderer = Renderer()
        renderer.string_encoding = 'ascii'

        engine = renderer._make_render_engine()
        literal = engine.literal

        self.assertEqual(literal(u"foo"), "foo")

    def test__literal__returns_unicode(self):
        """
        Test that literal returns unicode (and not a subclass).

        """
        renderer = Renderer()
        renderer.string_encoding = 'ascii'

        engine = renderer._make_render_engine()
        literal = engine.literal

        self.assertEqual(type(literal("foo")), unicode)

        class MyUnicode(unicode):
            pass

        s = MyUnicode("abc")

        self.assertEqual(type(s), MyUnicode)
        self.assertTrue(isinstance(s, unicode))
        self.assertEqual(type(literal(s)), unicode)

    ## Test the engine's escape attribute.

    def test__escape__uses_renderer_escape(self):
        """
        Test that escape uses the renderer's escape function.

        """
        renderer = Renderer()
        renderer.escape = lambda s: "**" + s

        engine = renderer._make_render_engine()
        escape = engine.escape

        self.assertEqual(escape("foo"), "**foo")

    def test__escape__uses_renderer_unicode(self):
        """
        Test that escape uses the renderer's unicode function.

        """
        renderer = Renderer()
        renderer.unicode = mock_unicode

        engine = renderer._make_render_engine()
        escape = engine.escape

        b = u"foo".encode('ascii')
        self.assertEqual(escape(b), "FOO")

    def test__escape__has_access_to_original_unicode_subclass(self):
        """
        Test that escape receives strings with the unicode subclass intact.

        """
        renderer = Renderer()
        renderer.escape = lambda s: unicode(type(s).__name__)

        engine = renderer._make_render_engine()
        escape = engine.escape

        class MyUnicode(unicode):
            pass

        self.assertEqual(escape(u"foo".encode('ascii')), unicode.__name__)
        self.assertEqual(escape(u"foo"), unicode.__name__)
        self.assertEqual(escape(MyUnicode("foo")), MyUnicode.__name__)

    def test__escape__returns_unicode(self):
        """
        Test that literal returns unicode (and not a subclass).

        """
        renderer = Renderer()
        renderer.string_encoding = 'ascii'

        engine = renderer._make_render_engine()
        escape = engine.escape

        self.assertEqual(type(escape("foo")), unicode)

        # Check that literal doesn't preserve unicode subclasses.
        class MyUnicode(unicode):
            pass

        s = MyUnicode("abc")

        self.assertEqual(type(s), MyUnicode)
        self.assertTrue(isinstance(s, unicode))
        self.assertEqual(type(escape(s)), unicode)

