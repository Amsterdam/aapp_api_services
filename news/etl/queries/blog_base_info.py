QUERY = """
query MyQuery($nodeID: Int!) {
  nodeByID(id: $nodeID){
    ... on Blog {
          id
          changedDate
    }
  }
}
"""
