# coding=utf8
"""Fluent AST helpers.

The functions defined in this module offer a shorthand for defining common AST
nodes.

They take a string argument and immediately return a corresponding AST node.
(As opposed to Transforms which are AST nodes on their own and only return the
migrated AST nodes when they are evaluated by a MergeContext.) """

from __future__ import unicode_literals
from __future__ import absolute_import

from fluent.syntax import FluentParser, ast as FTL
from .transforms import Transform, CONCAT, COPY
from .errors import NotSupportedError, InvalidTransformError


def EXTERNAL_ARGUMENT(name):
    """Create an ExternalArgument expression."""

    return FTL.ExternalArgument(
        id=FTL.Identifier(name)
    )


def MESSAGE_REFERENCE(name):
    """Create a MessageReference expression."""

    return FTL.MessageReference(
        id=FTL.Identifier(name)
    )


def transforms_from(ftl):
    """Parse FTL code into a list of Message nodes with Transforms.

    The FTL may use fabricated functions inside of placeables which will be
    converted into actual migration transforms if their names match.

        new-key = Hardcoded text { COPY("filepath.dtd", "string.key") }

    Only COPY is supported.
    """

    IMPLICIT_TRANSFORMS = ("CONCAT",)
    FORBIDDEN_TRANSFORMS = ("PLURALS", "REPLACE", "REPLACE_IN_TEXT")

    def into_transforms(node):
        """Convert { COPY() } placeables into the COPY() transform."""

        if isinstance(node, FTL.Junk):
            anno = node.annotations[0]
            raise InvalidTransformError(
                "Transform contains parse error: {}, at {}".format(
                    anno.message, anno.span.start))
        if isinstance(node, FTL.CallExpression):
            name = node.callee.name
            if name == "COPY":
                # Convert StringExpressions to string values.
                args = (arg.value for arg in node.args)
                return COPY(*args)
            if name in IMPLICIT_TRANSFORMS:
                raise NotSupportedError(
                    "{} may not be used with transforms_from(). It runs "
                    "implicitly on all Patterns anyways.".format(name))
            if name in FORBIDDEN_TRANSFORMS:
                raise NotSupportedError(
                    "{} may not be used with transforms_from(). It requires "
                    "additional logic in Python code.".format(name))
        if (isinstance(node, FTL.Placeable)
                and isinstance(node.expression, Transform)):
            # Replace the placeable with the transform it's holding.
            # Transforms evaluate to Patterns which aren't valid Placeable
            # expressions.
            return node.expression
        if isinstance(node, FTL.Pattern):
            # Replace the Pattern with CONCAT which is more accepting of its
            # elements. CONCAT takes PatternElements, Expressions and other
            # Patterns (e.g. returned from evaluating transforms).
            return CONCAT(*node.elements)
        return node

    parser = FluentParser(with_spans=False)
    resource = parser.parse(ftl)
    return resource.traverse(into_transforms).body
