#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LameJs - A very basic javascript interpreter in Python
# This file is part of the Wapiti project (http://wapiti.sourceforge.net)
# Copyright (C) 2013-2018 Nicolas Surribas
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import logging

from wapitiCore.net.jsparser import jsparser3


class LameJs:

    def __init__(self, data):
        self.js_vars = {}
        self.links = []
        self.debug = False
        try:
            self.js_vars = {}
            self.links = []
            rootnode = jsparser3.parse(data, None, 0)
            self.read_node(rootnode)
        except Exception:
            pass

    def get_vars(self):
        return self.js_vars

    def get_links(self):
        return self.links

    def read_node(self, node):
        if node.type == "SCRIPT":
            logging.debug("# SCRIPT")
            for sub_node in node:
                self.read_node(sub_node)
        elif node.type == "VAR":
            logging.debug("# VAR IN")
            logging.debug("# VAR OUT {}".format(self.read_node(node[0])))
        elif node.type == "IDENTIFIER":
            logging.debug("# IDENTIFIER")
            if hasattr(node, 'initializer'):
                value = self.read_node(node.initializer)
                self.js_vars[node.value] = value
                return node.value, value
            return node.value
        elif node.type == "NUMBER":
            logging.debug("# NUMBER")
            return node.value
        elif node.type == "STRING":
            logging.debug("# STRING")
            return node.value
        elif node.type == "PLUS":
            logging.debug("# PLUS")
            eax = None
            for sub_node in node:
                value = self.read_node(sub_node)
                if eax is None:
                    eax = value
                else:
                    if isinstance(eax, str):
                        if isinstance(value, str):
                            eax += value
                        elif isinstance(value, int):
                            eax += str(value)
                    elif isinstance(eax, int):
                        if isinstance(value, str):
                            eax = str(eax) + value
                        elif isinstance(value, int):
                            eax += value
            return eax
        elif node.type == "FUNCTION":
            logging.debug("# FUNCTION")
            try:
                func_name = node.name
            except AttributeError:
                func_name = "anonymous"
            logging.debug("In function {0}".format(func_name))
            self.read_node(node.body)
        elif node.type == "SEMICOLON":
            logging.debug("# SEMICOLON")
            self.read_node(node.expression)
            logging.debug("Semicolon end")
        elif node.type == "CALL":
            logging.debug("# CALL")
            func_name = self.read_node(node[0])
            if not func_name:
                func_name = "anonymous"
            params = self.read_node(node[1])
            logging.debug("func_name = {0}".format(func_name))
            logging.debug("params = {0}".format(params))
            if func_name == "window.open":
                if len(params):
                    self.links.append(params[0])
            elif func_name.endswith(".asyncRequest"):
                if len(params) > 1:
                    if params[0].upper() in ["GET", "POST"]:
                        self.links.append(params[1])
        elif node.type == "DOT":
            logging.debug("# DOT")
            return ".".join([sub_node.value for sub_node in node])
        elif node.type == "LIST":
            logging.debug("# LIST")
            ll = []
            for sub_node in node:
                ll.append(self.read_node(sub_node))
            logging.debug("list = {0}".format(ll))
            return ll
        elif node.type == "ASSIGN":
            logging.debug("# ASSIGN")
            left_value = self.read_node(node[0])
            right_value = self.read_node(node[1])
            logging.debug("left_value = {0}".format(left_value))
            logging.debug("right_value = {0}".format(right_value))
            if right_value and (
                left_value.endswith(".href") or
                left_value.endswith(".action") or
                left_value.endswith(".location") or
                left_value.endswith(".src")
            ):
                if node[1].type == "IDENTIFIER" and self.js_vars.get(right_value):
                    self.links.append(self.js_vars[right_value])
                else:
                    self.links.append(right_value)
        elif node.type == "WITH":
            logging.debug("# WITH")
            for sub_node in node.body:
                self.read_node(sub_node)
        elif node.type == "PROPERTY_INIT":
            logging.debug("# PROPERTY_INIT")
            attrib_name = self.read_node(node[0])
            attrib_value = self.read_node(node[1])
            logging.debug("attrib_name = {0}".format(attrib_name))
            logging.debug("attrib_value = {0}".format(attrib_value))
            return attrib_name
        elif node.type == "OBJECT_INIT":
            logging.debug("# OBJECT_INIT")
            for sub_node in node:
                self.read_node(sub_node)
            logging.debug("OBJECT_INIT end")
        elif node == "REGEXP":
            logging.debug("# REGEXP")
            return node.value
        elif node == "THIS":
            logging.debug("# THIS")
            return "this"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    data = """
    window.open("/toto.html");
    document.location='bidule.html';
    var link='ab'+'cd'+'.html';
    window.href=link;
    document.location = link + "?var=value";
    """

    # from https://public-firing-range.appspot.com/remoteinclude/script_hash.html
    data2 = """
    var target = location.hash.substr(1);
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = target;
    head.appendChild(script);
    """
    lame_js = LameJs(data)
    print(lame_js.get_links())
