QUERY = """
query MyQuery($paragraphId: Int!, $page: Int!) {
  view(paragraphId: $paragraphId, page: $page) {
    name
   ... on View {
      id
      name
      nodes {
        ... on News {
          id
          tag {
            id
            name
          }
          summaryShort
          title
          changedDate
          #displayChangedDate
          publicationDate
          #metaDescription
          path
          content {
            ... on ParagraphGrid {
              id
              rows {
                content {
                  ... on ParagraphDdsRichText {
                    id
                    content
                  }
                }
              }
            }
          }
          image {
            ... on Image {
              name
              src
            }
          }
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
