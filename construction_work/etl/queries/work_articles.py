QUERY = """
query PageView($paragraphId: Int!, $page: Int!) {
  view(paragraphId: $paragraphId, page: $page) {
    name
   ... on View {
      id
      name
      nodes {
        ... on Page {
          id
          tag {
            id
            name
          }
          summaryShort
          title
          changedDate
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
              alt
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
