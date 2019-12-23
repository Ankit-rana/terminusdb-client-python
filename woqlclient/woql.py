"""
  * The WOQL Query object implements the WOQL language via the fluent style
  * @param query - json version of query
  * @returns WOQLQuery object
"""

import sys
from copy import copy

#from .woql import WOQL

STANDARD_URLS = {
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'owl': 'http://www.w3.org/2002/07/owl#',
    'tcs': 'http://terminusdb.com/schema/tcs#',
    'tbs': 'http://terminusdb.com/schema/tbs#',
    'xdd': 'http://terminusdb.com/schema/xdd#',
    'v': 'http://terminusdb.com/woql/variable/',
    'terminus': 'http://terminusdb.com/schema/terminus#',
    'vio': 'http://terminusdb.com/schema/vio#',
    'docs': 'http://terminusdb.com/schema/documentation#'
}

class WOQLQuery:
    def __init__(self,query=None):
        self.query = query if query else {}
        self.cursor = self.query
        self.chain_ended = False
        self.contains_update = False
        # operators which preserve global paging
        self.paging_transitive_properties = ['select', 'from', 'start', 'when', 'opt', 'limit']
        self.vocab = self._loadDefaultVocabulary()
        # object used to accumulate triples from fragments to support usage like node("x").label("y")
        self.tripleBuilder = False

        self.cleanClass = self.cleanType = self.cleanPredicate
        self.relationship = self.entity

    def isLiteralType(self, t):
        if t:
            pref = t.split(":")
            if (pref[0] == "xdd" or pref[0] == "xsd"):
                return True
        return False

    def get(self, arr1, arr2, target=None):
        """Takes an array of variables, an optional array of column names"""
        if hasattr(arr1, 'json'):
            map = arr1.json()
            target = arr2;
        else:
            map = self.buildAsClauses(arr1, arr2);

        if target:
            if hasattr(target, 'json'):
                target = target.json()
            self.cursor['get'] = [map, target];
        else:
            self.cursor['get'] = [map, {}];
            self.cursor = self.cursor["get"][1];
        return self

    def buildAsClauses(self, vars=None, cols=None):
        clauses = []
        def check_vars_cols(obj):
            return obj and \
                   isinstance(obj, (list, dict, WOQLQuery)) and \
                   len(obj)
        if check_vars_cols(vars):
            for i in range(len(vars)):
                v = vars[i]
                if check_vars_cols(cols):
                    c = cols[i]
                    if type(c) == str:
                        c = {"@value": c}
                    clauses.append({'as': [c, v]})
                else:
                    if hasattr(a, 'as') or ('as' in a):
                        clauses.append(v)
                    else:
                        clauses.append({'as': [v]})
        return clauses

    def typecast(self, va, type, vb):
        self.cursor['typecast'] = [va, type, vb];
        return self

    def length(self, va, vb):
        self.cursor['length'] = [va, vb];
        return self

    def remote(self, json):
        self.cursor['remote'] = [json];
        return self

    def file(self, json):
        self.cursor['file'] = [json];
        return self

    # WOQL.group_by = function(gvarlist, groupedvar, groupquery, output){    return new WOQLQuery().group_by(gvarlist, groupedvar, groupquery, output); }

    def group_by(self, gvarlist, groupedvar, groupquery, output=None):
        args = []
        self.cursor['group_by'] = args
        if hasattr(gvarlist, 'json'):
            args.append(gvarlist.json())

        if 'list' in gvarlist:
            args.append(gvarlist)
        else:
            args.append({'list': gvarlist})

        if type(groupedvar) == list:
            ng = []
            for item in groupedvar:
                ng.append(item if (item[:2] == "v:") else "v:" + item)
            groupedvar = {"list": ng}
        elif type(groupedvar) == str:
            if groupedvar[:2] != "v:":
                groupedvar = "v:" + groupedvar

        args.append(groupedvar)

        if output:
            if hasattr(groupquery, 'json'):
                groupquery = groupquery.json()
            args.append(groupquery)
        else:
            output = groupquery
            sq = {}
            self.cursor = sq
            args.append(sq)

        if output[:2] != "v:":
            output = "v:" + output

        args.append(output)

        return self

    def idgen(self, prefix, vari, type, mode=None):
        self.cursor['idgen'] = [prefix]
        if hasattr(vari, 'json'):
            self.cursor['idgen'].append(vari.json())
        elif hasattr(vari, 'list') or ('list' in vari):
            self.cursor['idgen'].append(vari)
        else:
            self.cursor['idgen'].append({"list": vari})

        if mode:
            self.cursor['idgen'].append(mode)

        self.cursor['idgen'].append(type)
        return self

    def unique(self, prefix, vari, type):
        self.cursor['unique'] = [prefix]
        if hasattr(vari, 'json'):
            self.cursor['unique'].append(vari.json())
        elif hasattr(vari, 'list') or ('list' in vari):
            self.cursor['unique'].append(vari)
        else:
            self.cursor['unique'].append({"list": vari})

        self.cursor['unique'].append(type)
        return self

    def concat(self, list, v):
        if type(list) == str:
            nlist = list.split('/(v:[\w_]+)\b/')
            nxlist = []
            for i in range(1,len(nlist)):
                if (nlist[i-1][len(nlist[i-1])-1:] == "v") and \
                   (nlist[i][:1] == ":"):
                   nlist[i-1] = nlist[i-1][:len(nlist[i-1])-1]
                   nlist[i] = nlist[i][1:]
        elif 'list' in list:
            nlist = list['list']
        elif isinstance(list, (list, dict, WOQLQuery)):
            nlist = list
        args = []
        for item in nlist:
            if (not item):
                continue
            if type(item) == str:
                if item[:2] == "v:":
                    arg.append(item)
                else:
                    nvalue = {"@value": item, "@type": "xsd:string"}
                    args.append(nvalue)
            elif item:
                args.append(nlist[i])

        if v.find(":") == -1:
            v = "v:" + v

        self.cursor['concat'] = [{"list": args}, v]
        return self

    def lower(self, u, l):
        self.cursor['lower'] = [u, l]
        return self

    def pad(self, u, l):
        self.cursor['lower'] = [u, l]
        return self

    def join(self, *args):
        self.cursor['join'] = args
        return this

    def less(self, v1, v2):
        self.cursor['less'] = [v1, v2]
        return self

    def greater(self, v1, v2):
        self.cursor['greaters'] = [v1, v2]
        return self

    def list(self, *args):
        self.cursor['list'] = args
        return this

    def json(self, json=None):
        """json version of query for passing to api"""
        if json:
            self.query = json
            return self
        return self.query

    def when(self, Query, Update=None):
        """
        Functions which take a query as an argument advance the cursor to make the chaining of queries fall
        into the corrent place in the encompassing json
        """
        if type(Query) == bool:
            if Query:
                self.cursor["when"] = [{"true": []}, {}]
            else:
                self.cursor["when"] = [{"false": []}, {}]
        else:
            q =  Query.json() if hasattr(Query,'json') else Query
            self.cursor['when'] = [q, {}]

        if Update:
            upd = Update.json() if hasattr(Update,'json') else Update
            self.cursor["when"][1] = upd

        self.cursor = self.cursor["when"][1]
        return self

    def opt(self, query=None):
        if query:
            q = query.json() if callable(query.json) else query
            self.cursor["opt"] = [q]
        else:
            self.cursor['opt'] = [{}]
            self.cursor = self.cursor["opt"][0]
        return self

    def woql_from(self, dburl, query=None):
        self._advanceCursor("from", dburl)
        if query:
            self.cursor = query.json()
        return self

    def into(self, dburl, query=None):
        self._advanceCursor("into", dburl)
        if query:
            self.cursor = query.json()
        return self

    def limit(self, limit, query=None):
        self._advanceCursor("limit", limit)
        if query:
            self.cursor = query.json()
        return self

    def start(self, start, query=None):
        self._advanceCursor("start", start)
        if query:
            self.cursor = query.json()
        return self

    def select(self, *args):
        self.cursor['select'] = list(args)
        index = len(args)
        if isinstance(self.cursor['select'][index-1], (list, dict, WOQLQuery)):
            self.cursor['select'][index-1] = self.cursor['select'][index-1].json()
        else:
            self.cursor['select'].append({})
            self.cursor = self.cursor['select'][index]
        return self

    def woql_and(self, *args):
        self.cursor['and'] = []
        for item in args:
            if item.contains_update:
                self.contains_update = True
            self.cursor['and'].append(item.json())
        return self

    def woql_or(self, *args):
        self.cursor['or'] = []
        for item in args:
            if item.contains_update:
                self.contains_update = True
            self.cursor['or'].append(item.json())
        return self

    def woql_not(self, query=None):
        if query:
            if query.contains_update:
                self.contains_update = True
            self.cursor['not'] = [query.json()]
        else:
            self.cursor['not'] = [{}]
            self.cursor = self.cursor['not'][0]
        return self

    def triple(self, a, b, c):
        self.cursor["triple"] = [self.cleanSubject(a),self.cleanPredicate(b),self.cleanObject(c)]
        return self.last("triple", self.cleanSubject(a))

    def quad(self, a, b, c, g):
        self.cursor["quad"] = [self.cleanSubject(a),
                                self.cleanPredicate(b),
                                self.cleanObject(c),
                                self.cleanGraph(g)]
        return self.last("quad", self.cleanSubject(a))


    def eq(self, a, b):
        self.cursor["eq"] = [self.cleanObject(a),self.cleanObject(b)];
        return self.last()

    def sub(self, a, b=None):
        if (not b) and self.tripleBuilder:
            self.tripleBuilder.sub(self.cleanClass(a))
            return self
        self.cursor["sub"] = [self.cleanClass(a),self.cleanClass(b)]
        return self.last("sub", a)

    def comment(self, val=None):
        if val and hasattr(val, 'json'):
            self.cursor['comment'] = [val.json()]
        elif type(val) == str:
            self.cursor['comment'] = [{"@value": val, "@language": "en"}]
        elif isinstance(val, (list, dict, WOQLQuery)):
            if len(val):
                self.cursor['comment'] = val
            else:
                self.cursor['comment'] = [val]
        else:
            self.cursor['comment'] = []

        last_index = len(self.cursor['comment'])
        self.cursor['comment'].append({})
        self.cursor = self.cursor['comment'][last_index]
        return self

    def abstract(self, varname=None):
        if varname:
            return self.quad(varname, "tcs:tag", "tcs:abstract", "db:schema")
        elif self.tripleBuilder:
            self.tripleBuilder.abstract()
        return self

    def isa(self, a, b=None):
        if (not b) and self.tripleBuilder:
            self.tripleBuilder.isa(self.cleanClass(a))
            return self

        if b:
            self.cursor["isa"] = [self.cleanClass(a),self.cleanClass(b)]
            return self.last("isa", a)

    def trim(self, a, b):
        self.cursor['trim'] = [a, b]
        return self.last('trim', b)

    def eval(self, arith, v):
        if hasattr(arith, 'json'):
            arith = arith.json()
        self.cursor['eval'] = [arith, v]
        return self.last('eval', v)


    def plus(self, *args):
        self.cursor['plus'] = []
        for item in args:
            self.cursor['plus'].append(item.json() if hasattr(item,'json') else item)
        return self.last()

    def minus(self, *args):
        self.cursor['minus'] = []
        for item in args:
            self.cursor['minus'].append(item.json() if hasattr(item,'json') else item)
        return self.last()

    def times(self, *args):
        self.cursor['times'] = []
        for item in args:
            self.cursor['times'].append(item.json() if hasattr(item,'json') else item)
        return self.last()

    def divide(self, *args):
        self.cursor['divide'] = []
        for item in args:
            self.cursor['divide'].append(item.json() if hasattr(item,'json') else item)
        return self.last()

    def div(self, *args):
        self.cursor['div'] = []
        for item in args:
            self.cursor['div'].append(item.json() if hasattr(item,'json') else item)
        return self.last()

    def exp(self, a, b):
        if hasattr(a, 'json'):
            a = a.json()
        if hasattr(b, 'json'):
            b = b.json()

        self.cursor['exp'] = [a, b]
        return self.last()

    def delete(self, JSON_or_IRI):
        self.cursor['delete'] = [JSON_or_IRI]
        return self.lastUpdate()

    def delete_triple(self, Subject, Predicate, Object_or_Literal):
        self.cursor['delete_triple'] = [self.cleanSubject(Subject),
                                        self.cleanPredicate(Predicate),
                                        self.cleanObject(Object_or_Literal)]
        return self.lastUpdate('delete_triple', self.cleanSubject(Subject))

    def add_triple(self, Subject, Predicate, Object_or_Literal):
        self.cursor['add_triple'] = [self.cleanSubject(Subject),
                                    self.cleanPredicate(Predicate),
                                    self.cleanObject(Object_or_Literal)]
        return self.lastUpdate('add_triple', self.cleanSubject(Subject))

    def delete_quad(self, Subject, Predicate, Object_or_Literal, Graph):
        self.cursor['delete_quad'] =[self.cleanSubject(Subject),
                                    self.cleanPredicate(Predicate),
                                    self.cleanObject(Object_or_Literal),
                                    self.cleanGraph(Graph)]
        return self.lastUpdate('delete_quad', self.cleanSubject(Subject))

    def add_quad(self, Subject, Predicate, Object_or_Literal, Graph):
        self.cursor['add_quad'] =[self.cleanSubject(Subject),
                                    self.cleanPredicate(Predicate),
                                    self.cleanObject(Object_or_Literal),
                                    self.cleanGraph(Graph)]
        return self.lastUpdate('add_quad', self.cleanSubject(Subject))

    def update(self, woql):
        self.cursor['update'] = [ woql.json() ]
        return self.lastUpdate()

    # Schema manipulation shorthand

    def addClass(self, c=None, graph=None):
        if c:
            graph = self.cleanGraph(graph) if graph else "db:schema"
            c = "scm:" + c if c.find(":") == -1 else c
            self.add_quad(c, "rdf:type", "owl:Class", graph)
        return self

    def deleteClass(self, c=None, graph=None):
        if c:
            graph = self.cleanGraph(graph) if graph else "db:schema"
            c = "scm:" + c if c.find(":") == -1 else c

            return self.woql_and(WOQLQuery().delete_quad(c, "v:All", "v:Al2", graph),
                            WOQLQuery().opt().delete_quad("v:Al3", "v:Al4", c, graph))
        return self

    def addProperty(self, p=None, t=None, g=None):
        if not t:
            t = "xsd:string"
        if p:
            graph = self.cleanGraph(g) if g else "db:schema"
            p = "scm:" + p if p.find(":") == -1 else p
            t = self.cleanType(t) if t.find(":") == -1 else t
            tc = self.cursor
            if WOQLQuery().isLiteralType(t):
                self.woql_and(WOQLQuery().add_quad(p, "rdf:type", "owl:DatatypeProperty", graph),
                         WOQLQuery().add_quad(p, "rdfs:range", t, graph))
            else:
                self.woql_and(WOQLQuery().add_quad(p, "rdf:type", "owl:ObjectProperty", graph),
                         WOQLQuery().add_quad(p, "rdfs:range", t, graph))
        return self.lastUpdate("add_quad", self.cleanClass(p))

    def deleteProperty(self, p=None, graph=None):
        if p:
            graph = self.cleanGraph(graph) if graph else "db:schema"
            p = "scm:" + p if p.find(":") == -1 else p
            return self.woql_and(WOQLQuery().delete_quad(p, "v:All", "v:Al2", graph),
                            WOQLQuery().delete_quad("v:Al3", "v:Al4", p, graph))
        return self

    # Language elements that cannot be invoked from the top level and therefore are not exposed in the WOQL api

    def woql_as(self, a=None, b=None):
        if (not a) or (not b):
            return

        if not hasattr(self, 'asArray'):
            self.asArray = True
            self.query = []

        if b.find(":") == -1:
            b = "v:" + b

        if isinstance(a, (list, dict, WOQLQuery)):
            val = a
        else:
            val = { "@value" : a}

        self.query.append({'as': [val, b]})
        return self

    # WOQL API

    def node(self, node, type=None):
        if not type:
            type = "triple"
        self.tripleBuilder = TripleBuilder(type, self.cursor, node)
        return self

    def graph(self, g):
        g = self.cleanGraph(g)
        if hasattr(self,'type'):
            t = "quad" if self.type == "triple" else False
            if self.type == "add_triple":
                t = "add_quad"
            if self.type == "delete_triple":
                t = "delete_quad"
        if not self.tripleBuilder:
            self.tripleBuilder = TripleBuilder(t, self.cursor)
        self.tripleBuilder.graph(g)
        return self

    def label(self, l, lang=None):
        if self.tripleBuilder:
            self.tripleBuilder.label(l, lang)
        return self

    def description(self, c, lang=None):
        if self.tripleBuilder:
            self.tripleBuilder.description(c, lang)
        return self

    def domain(self, d):
        d = self.cleanClass(d)
        if self.tripleBuilder:
            self.tripleBuilder.addPO('rdfs:domain',d)
        return self

    def parent(self, *args):
        if self.tripleBuilder:
            for item in args:
                pn = self.cleanClass(item)
                self.tripleBuilder.addPO('rdfs:subClassOf', pn)
        return self

    def entity(self, *args):
        return self.parent("tcs:Entity")

    def property(self, p,val):
        if self.tripleBuilder:
            p = self.cleanPredicate(p)
            self.tripleBuilder.addPO(p, val)
        return self

    def max(self, m):
        if self.tripleBuilder:
            self.tripleBuilder.card(m, "max")
        return self

    def cardinality(self, m):
        if self.tripleBuilder:
            self.tripleBuilder.card(m, "cardinality")
        return self

    def min(self, m):
        if self.tripleBuilder:
            self.tripleBuilder.card(m, "min")
        return self

    def star(self, GraphIRI=None, Subj=None, Pred=None, Obj=None):
        Subj = self.cleanSubject(Subj) if Subj else "v:Subject"
        Pred = self.cleanPredicate(Pred) if Pred else "v:Predicate"
        Obj = self.cleanObject(Obj) if Obj else "v:Object"
        GraphIRI = self.cleanGraph(GraphIRI) if GraphIRI else False

        if GraphIRI:
            return self.quad(Subj, Pred, Obj, GraphIRI)
        else:
            return self.triple(Subj, Pred, Obj)

    def getEverything(self, GraphIRI=None):
        if GraphIRI:
            GraphIRI = self.cleanGraph(GraphIRI)
            return self.quad("v:Subject", "v:Predicate", "v:Object", GraphIRI)
        else:
            self.triple("v:Subject", "v:Predicate", "v:Object")

    def getAllDocuments(self):
        return self.woql_and(
                    WOQLQuery().triple("v:Subject", "rdf:type", "v:Type"),
                    WOQLQuery().sub("v:Type", "tcs:Document")
                    )

    def documentMetadata(self):
        return self.woql_and(
                WOQLQuery().triple("v:ID", "rdf:type", "v:Class"),
                WOQLQuery().sub("v:Class", "tcs:Document"),
                WOQLQuery().opt().triple("v:ID", "rdfs:label", "v:Label"),
                WOQLQuery().opt().triple("v:ID", "rdfs:comment", "v:Comment"),
                WOQLQuery().opt().quad("v:Class", "rdfs:label", "v:Type", "db:schema"),
                WOQLQuery().opt().quad("v:Class", "rdfs:comment", "v:Type_Comment", "db:schema")
                )

    def concreteDocumentClasses(self):
        return self.woql_and(
                WOQLQuery().sub("v:Class", "tcs:Document"),
                WOQLQuery().woql_not().abstract("v:Class"),
                WOQLQuery().opt().quad("v:Class", "rdfs:label", "v:Label", "db:schema"),
                WOQLQuery().opt().quad("v:Class", "rdfs:comment", "v:Comment", "db:schema")
                )

    def propertyMetadata(self):
        return self.woql_and(
                WOQLQuery().woql_or(
                    WOQLQuery().quad("v:Property", "rdf:type", "owl:DatatypeProperty", "db:schema"),
                    WOQLQuery().quad("v:Property", "rdf:type", "owl:ObjectProperty", "db:schema")
                ),
                WOQLQuery().opt().quad("v:Property", "rdfs:range", "v:Range", "db:schema"),
                WOQLQuery().opt().quad("v:Property", "rdf:type", "v:Type", "db:schema"),
                WOQLQuery().opt().quad("v:Property", "rdfs:label", "v:Label", "db:schema"),
                WOQLQuery().opt().quad("v:Property", "rdfs:comment", "v:Comment", "db:schema"),
                WOQLQuery().opt().quad("v:Property", "rdfs:domain", "v:Domain", "db:schema")
                )

    def elementMetadata(self):
        return self.woql_and(
                WOQLQuery().quad("v:Element", "rdf:type", "v:Type", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "tcs:tag", "v:Abstract", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:label", "v:Label", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:comment", "v:Comment", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:subClassOf", "v:Parent", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:domain", "v:Domain", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:range", "v:Range", "db:schema")
                )

    def classMetadata(self):
        return self.woql_and(
                WOQLQuery().quad("v:Element", "rdf:type", "owl:Class", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:label", "v:Label", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "rdfs:comment", "v:Comment", "db:schema"),
                WOQLQuery().opt().quad("v:Element", "tcs:tag", "v:Abstract", "db:schema")
                )

    def getDataOfClass(self, chosen):
        return self.woql_and(
                WOQLQuery().triple("v:Subject", "rdf:type", chosen),
                WOQLQuery().opt().triple("v:Subject", "v:Property", "v:Value")
                )

    def getDataOfProperty(self, chosen):
        return self.woql_and(
                WOQLQuery().triple("v:Subject", chosen, "v:Value"),
                WOQLQuery().opt().triple("v:Subject", "rdfs:label", "v:Label")
                )

    def documentProperties(self, id):
        return self.woql_and(
                WOQLQuery().triple(id, "v:Property", "v:Property_Value"),
                WOQLQuery().opt().quad("v:Property", "rdfs:label", "v:Property_Label", "db:schema"),
                WOQLQuery().opt().quad("v:Property", "rdf:type", "v:Property_Type", "db:schema")
                )

    def getDocumentConnections(self, id):
        return self.woql_and(
                WOQLQuery().woql_or(
                    WOQLQuery().triple(id, "v:Outgoing", "v:Entid"),
                    WOQLQuery().triple("v:Entid", "v:Incoming", id)
                ),
                WOQLQuery().isa("v:Entid", "v:Enttype"),
                WOQLQuery().sub("v:Enttype", "tcs:Document"),
                WOQLQuery().opt().triple("v:Entid", "rdfs:label", "v:Label"),
                WOQLQuery().opt().quad("v:Enttype", "rdfs:label", "v:Class_Label", "db:schema")
                )

    def getInstanceMeta(self, url):
        return self.woql_and(
                WOQLQuery().triple(url, "rdf:type", "v:InstanceType"),
                WOQLQuery().opt().triple(url, "rdfs:label", "v:InstanceLabel"),
                WOQLQuery().opt().triple(url, "rdfs:comment", "v:InstanceComment"),
                WOQLQuery().opt().quad("v:InstanceType", "rdfs:label", "v:ClassLabel", "db:schema")
                )

    def simpleGraphQuery(self):
        return self.woql_and(
                WOQLQuery().triple("v:Source", "v:Edge", "v:Target"),
                WOQLQuery().isa("v:Source", "v:Source_Class"),
                WOQLQuery().sub("v:Source_Class", "tcs:Document"),
                WOQLQuery().isa("v:Target", "v:Target_Class"),
                WOQLQuery().sub("v:Target_Class", "tcs:Document"),
                WOQLQuery().opt().triple("v:Source", "rdfs:label", "v:Source_Label"),
                WOQLQuery().opt().triple("v:Source", "rdfs:comment", "v:Source_Comment"),
                WOQLQuery().opt().quad("v:Source_Class", "rdfs:label", "v:Source_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Source_Class", "rdfs:comment", "v:Source_Type_Comment", "db:schema"),
                WOQLQuery().opt().triple("v:Target", "rdfs:label", "v:Target_Label"),
                WOQLQuery().opt().triple("v:Target", "rdfs:comment", "v:Target_Comment"),
                WOQLQuery().opt().quad("v:Target_Class", "rdfs:label", "v:Target_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Target_Class", "rdfs:comment", "v:Target_Type_Comment", "db:schema"),
                WOQLQuery().opt().quad("v:Edge", "rdfs:label", "v:Edge_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Edge", "rdfs:comment", "v:Edge_Type_Comment", "db:schema")
                )

    def simpleGraphQuery(self):
        return self.woql_and(
                WOQLQuery().triple("v:Source", "v:Edge", "v:Target"),
                WOQLQuery().isa("v:Source", "v:Source_Class"),
                WOQLQuery().sub("v:Source_Class", "tcs:Document"),
                WOQLQuery().isa("v:Target", "v:Target_Class"),
                WOQLQuery().sub("v:Target_Class", "tcs:Document"),
                WOQLQuery().opt().triple("v:Source", "rdfs:label", "v:Source_Label"),
                WOQLQuery().opt().triple("v:Source", "rdfs:comment", "v:Source_Comment"),
                WOQLQuery().opt().quad("v:Source_Class", "rdfs:label", "v:Source_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Source_Class", "rdfs:comment", "v:Source_Type_Comment", "db:schema"),
                WOQLQuery().opt().triple("v:Target", "rdfs:label", "v:Target_Label"),
                WOQLQuery().opt().triple("v:Target", "rdfs:comment", "v:Target_Comment"),
                WOQLQuery().opt().quad("v:Target_Class", "rdfs:label", "v:Target_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Target_Class", "rdfs:comment", "v:Target_Type_Comment", "db:schema"),
                WOQLQuery().opt().quad("v:Edge", "rdfs:label", "v:Edge_Type", "db:schema"),
                WOQLQuery().opt().quad("v:Edge", "rdfs:comment", "v:Edge_Type_Comment", "db:schema")
                )

    def getVocabulary(self):
        return self.vocab

    def setVocabulary(self, vocab):
        """Provides the query with a 'vocabulary' a list of well known predicates that can be used without prefixes mapping: id: prefix:id ..."""
        self.vocab = vocab

    def loadVocabulary(self, client):
        """
        * Queries the schema graph and loads all the ids found there as vocabulary that can be used without prefixes
        * ignoring blank node ids
        """
        nw = WOQLQuery().quad("v:S", "v:P", "v:O", "db:schema")
        result = nw.execute(client)
        if (result and 'bindings' in result) and (len(result['bindings']) > 0):
            for item in result['bindings']:
                for key in item:
                    value = item[key]
                    if type(value) == str:
                        val_spl = value.split(":")
                        if len(val_spl)==2 and val_spl[1] and val_spl[0]!='_':
                            self.vocab[val_spl[1]] = value

    def getLimit(self):
        return self.getPagingProperty("limit")

    def setLimit(self, l):
        return self.setPagingProperty("limit", l)

    def isPaged(self, q=None):
        if q is None:
            q = self.query
        for prop in q:
            if prop == "limit":
                return True
            elif prop in self.paging_transitive_properties:
                return self.isPaged(q[prop][len(q[prop])-1])
        return False

    def getPage(self):
        if self.isPaged():
            psize = self.getLimit()
            if self.hasStart():
                s = self.getStart()
                return ((s // psize) + 1)
            else:
                return 1
        else:
            return False

    def setPage(self, pagenum):
        pstart = (self.getLimit() * (pagenum - 1))
        if self.hasStart():
            self.setStart(pstart)
        else:
            self.addStart(pstart)
        return self

    def nextPage(self):
        return self.setPage(self.getPage() + 1)

    def firstPage(self):
        return self.setPage(1)

    def previousPage(self):
        npage = self.getPage() - 1
        if npage > 0:
            self.setPage(npage)
        return self

    def setPageSize(self, size):
        self.setPagingProperty("limit", size)
        if self.hasStart():
            self.setStart(0)
        else:
            self.addStart(0)
        return self

    def hasSelect(self):
        return bool(self.getPagingProperty("select"))

    def getSelectVariables(self, q=None):
        if q is None:
            q = self.query
        for prop in q:
            if prop == "select":
                vars = q[prop][:len(q[prop])-1]
                return vars
            elif prop in self.paging_transitive_properties:
                val = self.getSelectVariables(q[prop][len(q[prop])-1])
                if val is not None:
                    return val

    def hasStart(self):
        result = self.getPagingProperty("start")
        return result is not None

    def getStart(self):
        return self.getPagingProperty("start");

    def setStart(self, start):
        return self.setPagingProperty("start", start)

    def addStart(self, s):
        if self.hasStart():
            self.setStart(s)
        else:
            nq = {'start': [s, self.query]}
            self.query = nq
        return self

    def getPagingProperty(self, pageprop, q=None):
        """Returns the value of one of the 'paging' related properties (limit, start,...)"""
        if q is None:
            q = self.query
        for prop in q:
            if prop == pageprop:
                return q[prop][0]
            elif prop in self.paging_transitive_properties:
                val = self.getPagingProperty(pageprop, q[prop][len(q[prop])-1])
                if val is not None:
                    return val

    def setPagingProperty(self, pageprop, val, q=None):
        """Sets the value of one of the paging_transitive_properties properties"""
        if q is None:
            q = self.query
        for prop in q:
            if prop == pageprop:
                q[prop][0] = val
            elif prop in self.paging_transitive_properties:
                self.setPagingProperty(pageprop, val, q[prop][len(q[prop])-1])
        return self


    def getContext(self, q=None):
        """Retrieves the value of the current json-ld context"""
        if q is None:
            q = self.query
        for prop in q:
            if prop == "@context":
                return q[prop]
            if prop in self.paging_transitive_properties:
                nc = self.getContext(q[prop][1])
            if nc:
                return nc

    def context(self, c):
        """Retrieves the value of the current json-ld context"""
        self.cursor['@context'] = c

    #Internal State Control Functions
    #Not part of public API -

    def _defaultContext(self, DB_IRI):
        result = copy(STANDARD_URLS)
        result['scm'] = DB_IRI + "/schema#"
        result['doc'] = DB_IRI + "/document/"
        result['db'] = DB_IRI + "/"
        return result

    def _loadDefaultVocabulary(self):
        vocab = {}
        vocab['type'] = "rdf:type"
        vocab['label'] = "rdfs:label"
        vocab['Class'] = "owl:Class"
        vocab['DatatypeProperty'] = "owl:DatatypeProperty"
        vocab['ObjectProperty'] = "owl:ObjectProperty"
        vocab['Entity'] = "tcs:Entity"
        vocab['Document'] = "tcs:Document"
        vocab['Relationship'] = "tcs:Relationship"
        vocab['temporality'] = "tcs:temporality"
        vocab['geotemporality'] = "tcs:geotemporality"
        vocab['geography'] = "tcs:geography"
        vocab['abstract'] = "tcs:abstract"
        vocab['comment'] = "rdfs:comment"
        vocab['range'] = "rdfs:range"
        vocab['domain'] = "rdfs:domain"
        vocab['subClassOf'] = "rdfs:subClassOf"
        vocab['string'] = "xsd:string"
        vocab['integer'] = "xsd:integer"
        vocab['decimal'] = "xsd:decimal"
        vocab['email'] = "xdd:email"
        vocab['json'] = "xdd:json"
        vocab['dateTime'] = "xsd:dateTime"
        vocab['date'] = "xsd:date"
        vocab['coordinate'] = "xdd:coordinate"
        vocab['line'] = "xdd:coordinatePolyline"
        vocab['polygon'] = "xdd:coordinatePolygon"
        return vocab

    def _advanceCursor(self, action, value):
        """Advances internal cursor to support chaining of calls: limit(50).start(50). rather than (limit, [50, (start, [50, (lisp-style (encapsulation)))))"""
        self.cursor[action] = [value]
        self.cursor[action].append({})
        self.cursor = self.cursor[action][1]

    def cleanSubject(self, s):
        if type(s) != str or s.find(":") != -1:
            return s
        if self.vocab and (s in self.vocab):
            return self.vocab[s]
        return "doc:" + s

    def cleanPredicate(self, p):
        if p.find(":") != -1:
            return p
        if self.vocab and (p in self.vocab):
            return self.vocab[p]
        return "scm:" + p

    def cleanGraph(self, g):
        if g.find(":") != -1:
            return g
        if self.vocab and (g in self.vocab):
            return self.vocab[g]
        return "db:" + g

    def cleanObject(self, o):
        if type(o) != str or o.find(":") != -1:
            return o
        if self.vocab and (o in self.vocab):
            return self.vocab[o]
        return { "@value": o, "@language": "en"}

    def last(self, call=None, subject=None):
        self.chain_ended = True
        if call:
            self.tripleBuilder = TripleBuilder(call, self.cursor, self.cleanSubject(subject))
        return self

    def lastUpdate(self, call=None, subj=None):
        """Called to indicate that this is the last call that is chainable - for example triple pattern matching.."""
        self.contains_update = True
        ret = self.last(call, subj)
        return ret

    def execute(self, client):
        """Executes the query using the passed client to connect to a server"""
        if "@context" not in self.query:
            self.query['@context'] = self._defaultContext(client.conConfig.dbURL())
        json = self.json()
        if self.contains_update:
            return client.select(json)
            #return client.update(json)
        else:
            return client.select(json)


class TripleBuilder:
    """
    * higher level composite queries - not language or api elements
    * Class for enabling building of triples from pieces
    * type is add_quad / remove_quad / add_triple / remove_triple
    """

    def __init__(self, type=None, cursor=None, s=None):
        self.type = type
        self.cursor = cursor
        self.subject = s if s else False
        self.g = False

        self.sub = self.isa

    def label(self, l, lang=None):
        if not lang:
            lang = "en"
        if l[:2] == "v:":
            d = {"value": l, "@language": lang }
        else:
            d = {"@value": l, "@language": lang }
        x = self.addPO('rdfs:label', d)
        return x

    def description(self, l, lang=None):
        if not lang:
            lang = "en"
        if l[:2] == "v:":
            d = {"value": l, "@language": lang }
        else:
            d = {"@value": l, "@language": lang }
        x = self.addPO('rdfs:comment', d)
        return x

    def addPO(self, p, o, g=None):
        if self.type:
            if self.type == "isa" or self.type == "sub":
                ttype = "triple"
            else:
                ttype = self.type
        else:
            ttype = "triple"

        evstr = ttype + '("' + self.subject + '", "' + p + '", '
        if type(o) == str:
            evstr += "'" + o + "'"
        elif isinstance(o, (list, dict, WOQLQuery)):
            evstr += str(o)
        else:
            evstr += o

        if ttype[-4:] == "quad" or self.g:
            if not g:
                g = self.g if self.g else "db:schema"
            evstr += ', "' + g + '"'
        evstr += ")"
        try:
            unit = eval("WOQLQuery()." + evstr)
            return self.addEntry(unit)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return self

    def getO(self, s, p):
        if self.cursor['and']:
            for item in self.cursor['and']:
                clause = item
                key = list(clause.keys())[0]
                if clause[key][0] == s and \
                   clause[key][1] == p and \
                   clause[key][2] :
                    return clause[key][2]
        elif self.cursor.keys():
            clause = self.cursor
            key = list(clause.keys())[0]
            if clause[key][0] == s and \
               clause[key][1] == p and \
               clause[key][2] :
                return clause[key][2]

        return False

    def addEntry(self, unit):
        if self.type in self.cursor:
            next = {}
            next[self.type] = self.cursor[self.type]
            self.cursor['and'] = [next]
            del self.cursor[self.type]

        if 'and' in self.cursor:
            self.cursor['and'].append(unit.json())
        else:
            j = unit.json()
            if self.type in j:
                self.cursor[self.type] = j[self.type]
            else:
                print(j)
        return self

    def card(self, n, which):
        os = self.subject
        self.subject += "_" + which
        self.addPO('rdf:type', "owl:Restriction")
        self.addPO("owl:onProperty", os)
        if which == "max":
            self.addPO("owl:maxCardinality", {"@value": n, "@type": "xsd:nonNegativeInteger"})
        elif which == "min":
            self.addPO("owl:minCardinality", {"@value": n, "@type": "xsd:nonNegativeInteger"})
        else:
            self.addPO("owl:cardinality", {"@value": n, "@type": "xsd:nonNegativeInteger"})

        od = self.getO(os, "rdfs:domain")
        if od:
            x = self.subject
            self.subject = od
            self.addPO("rdfs:subClassOf", self.subject)
        self.subject = os
        return self

    def isa(self, a):
        unit = WOQLQuery.isa(self.subject, a)
        self.addEntry(unit)

    def graph(self, g):
        self.g = g

    def abstract(self):
        return self.addPO('tcs:tag', "tcs:abstract")

"""

Methods that has not been impremented
====================================

/*
* Transforms from internal json representation to human writable WOQL.js format
*/
WOQLQuery.prototype.prettyPrint = function(indent, show_context, q, fluent){
    if(!this.indent) this.indent = indent;
    q = (q ? q : this.query);
    var str = "";
    const newlining_operators = ["get", "from", "into"];
    for(var operator in q){
    //ignore context in pretty print
    if(operator == "@context") {
    if( show_context){
    var c = this.getContext();
    if(c) str += "@context: " + JSON.stringify(c) + "\n";
    }
    continue;
    }
    //statement starts differently depending on indent and whether it is fluent style or regular function style
    str += this.getWOQLPrelude(operator, fluent, indent - this.indent);
    var val = q[operator];
    if(this.chainable(operator, val[val.length-1])){
    //all arguments up until the last are regular function arguments
    str += this.uncleanArguments(operator,  val.slice(0, val.length-1), indent, show_context);
    if(newlining_operators.indexOf(operator) !== -1){
    //some fluent function calls demand a linebreak..
    str += "\n" + nspaces(indent-this.indent);
    }
    //recursive call to query included in tail
    str += this.prettyPrint(indent, show_context, val[val.length-1], true);
    }
    else {
    //non chainable operators all live inside the function call parameters
    str += this.uncleanArguments(operator,  val, indent, show_context);
    }
    }
    //remove any trailing dots in the chain (only exist in incompletely specified queries)
    if(str.substring(str.length-1) == "."){
    str = str.substring(0, str.length-1);
    }
    return str;
}

/**
 * Gets the starting characters for a WOQL query - varies depending on how the query is invoked and how indented it is
 */
WOQLQuery.prototype.getWOQLPrelude = function(operator, fluent, inline){
    if(operator === "true" || operator === "false"){
    return operator;
    }
    if(fluent){
    return "." + operator;
    }
    return (inline ? "\n" + nspaces(inline) : "") + "WOQL." + operator;
}

/**
 * Determines whether a given operator can have a chained query as its last argument
 */
WOQLQuery.prototype.chainable = function(operator, lastArg){
    const non_chaining_operators = ["and", "or"];
    if(lastArg && typeof lastArg == "object" && typeof lastArg['@value'] == "undefined"  && typeof lastArg['@type'] == "undefined"  && typeof lastArg['value'] == "undefined" && non_chaining_operators.indexOf(operator) == -1){
    return true;
    }
    return false;
}

/**
 * Transforms arguments to WOQL functions from the internal (clean) version, to the WOQL.js human-friendly version
 */
WOQLQuery.prototype.uncleanArguments = function(operator, args, indent, show_context){
    str = '(';
    const args_take_newlines = ["and", "or"];
    if(this.hasShortcut(operator, args)){
    return this.getShortcut(args, indent);
    }
    else {
    for(var i = 0; i<args.length; i++){
    if(this.argIsSubQuery(operator, args[i], i)){
    str += this.prettyPrint(indent + this.indent, show_context, args[i], false);
    }
    else if(operator == "get" && i == 0){ // weird one, needs special casing
    str += "\n" + nspaces(indent-this.indent) + "WOQL";
    for(var j = 0; j < args[0].length; j++){
    var myas = (args[0][j].as ? args[0][j].as : args[0][j]);
    var lhs = myas[0];
    var rhs = myas[1];
    if(typeof lhs == "object" && lhs['@value']){
    lhs = lhs['@value'];
    }
    if(typeof lhs == "object") {
    lhs = JSON.stringify(lhs);
    }
    else {
    lhs = '"' + lhs + '"'
    }
    str += '.as(' + lhs;
    if(rhs) str += ', "' + rhs + '"';
    str += ")";
    str += "\n" + nspaces(indent);
    }
    }
    else {
    str += this.uncleanArgument(operator, args[i], i, args);
    }
    if(i < args.length -1) str +=  ',';
    }
    }
    if(args_take_newlines.indexOf(operator) != -1){
    str += "\n" + nspaces(indent-this.indent);
    }
    str += ")";
    return str;
}


/**
 * Passed as arguments: 1) the operator (and, triple, not, opt, etc)
 * 2) the value of the argument
 * 3) the index (position) of the argument.
 */
WOQLQuery.prototype.uncleanArgument = function(operator, val, index, allArgs){
    //numeric values go out untouched...
    const numeric_operators = ["limit", "start", "eval", "plus", "minus", "times", "divide", "exp", "div"];
    if(operator == "isa"){
    val = (index == 0 ? this.unclean(val, 'subject') : this.unclean(val, 'class'));
    }
    else if(operator == "sub"){
    val = this.unclean(val, 'class');
    }
    else if(["select"].indexOf(operator) != -1){
    if(val.substring(0, 2) == "v:") val = val.substring(2);
    }
    else if(["quad", "add_quad", "delete_quad", "add_triple", "delete_triple", "triple"].indexOf(operator) != -1){
    switch(index){
    case 0: val = this.unclean(val, "subject"); break;
    case 1: val = this.unclean(val, "predicate"); break;
    case 2: val = this.unclean(val, "object"); break;
    case 3: val = this.unclean(val, "graph"); break;
    }
    }
    if(typeof val == "object"){
    if(operator == "concat" && index == 0){
    var cstr = "";
    if(val.list){
    for(var i = 0 ; i<val.list.length; i++){
    if(val.list[i]['@value']) cstr += val.list[i]['@value'];
    else cstr += val.list[i];
    }
    }
    var oval = '"' + cstr + '"';
    }
    else {
    var oval = this.uncleanObjectArgument(operator, val, index);
    }
    return oval;
    }
    //else if(numeric_operators.indexOf(operator) !== -1){
    //    return val;
    //}
    if(typeof val == "string"){
    return '"' + val + '"';
    }
    return val;
}

WOQLQuery.prototype.uncleanObjectArgument = function(operator, val, index){
    if(val['@value'] && (val['@language'] || (val['@type'] && val['@type'] == "xsd:string"))) return '"' + val['@value'] + '"';
    if(val['@value'] && (val['@type'] && val['@type'] == "xsd:integer")) return val['@value'];
    if(val['list']) {
    var nstr = "[";
    for(var i = 0 ; i<val['list'].length; i++){
    if(typeof val['list'][i] == "object"){
    nstr += this.uncleanObjectArgument("list", val['list'][i], i);
    }
    else {
    nstr += '"' + val['list'][i] + '"';
    }
    if(i < val['list'].length-1){
    nstr += ",";
    }
    }
    nstr += "]";
    return nstr;
    }
    return JSON.stringify(val);
}

WOQLQuery.prototype.argIsSubQuery = function(operator, arg, index){
    const squery_operators = ["and", "or", "when", "not", "opt", "exp", "minus", "div", "divide", "plus", "multiply"];
    if(squery_operators.indexOf(operator) !== -1){
    if(arg && typeof arg != "object") return false;
    return true;
    }
    if(operator == "group_by" && index == 2) return true;
    else return false;
}

/**
 * Goes from the properly prefixed clean internal version of a variable to the WOQL.js unprefixed form
 */
WOQLQuery.prototype.unclean = function(s, part){
    if(typeof s != "string") return s;
    if(s.indexOf(":") == -1) return s;
    if(s.substring(0,4) == "http") return s;
    var suff = s.split(":")[1];
    if(this.vocab && this.vocab[suff] && this.vocab[suff] == s){
    return suff;
    }
    if(!part) return s;
    if(part == "subject" && (s.split(":")[0] == "doc")) return suff;
    if(part == "class" && (s.split(":")[0] == "scm")) return suff;
    if(part == "predicate" && (s.split(":")[0] == "scm")) return suff;
    if(part == "type" && (s.split(":")[0] == "scm")) return suff;
    if(part == "graph" && (s.split(":")[0] == "db")) return suff;
    return s;
}

WOQLQuery.prototype.hasShortcut = function(operator, args, indent, show_context){
    if(operator == "true") return true;
}

WOQLQuery.prototype.getShortcut = function(operator, args, indent, show_context){
    if(operator == "true") return true;
}

function nspaces(n){
    let spaces = "";
    for(var i = 0; i<n; i++){
    spaces += " ";
    }
    return spaces;
}

WOQLQuery.prototype.printLine = function(indent, clauses){
    return "(\n" + nspaces(indent) + "WOQL." + clauses.join(",\n"+ nspaces(indent) + "WOQL.") + "\n" + nspaces(indent - this.indent) + ")";
}

"""
