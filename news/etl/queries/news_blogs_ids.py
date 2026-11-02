QUERY = """
query NewsAndBlogsIds($paragraphId: Int!, $page: Int!) {
  view(paragraphId: $paragraphId, page: $page) {
    name
   ... on View {
      id
      name
      nodes {
        ... on News {
          __typename
          id
        }
        ... on Blog {
          __typename
          id
        }
      }
      itemsPerPage
      highlightedNumber
    }
    pagination {
      totalPages
      previousPage
      nextPage
      enabled
      currentPage
    }
  }
}
"""
