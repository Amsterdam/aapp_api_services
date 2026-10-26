QUERY = """
query MyQuery($paragraphId: Int!, $page: Int!) {
  view(paragraphId: $paragraphId, page: $page) {
    name
   ... on View {
      id
      name
      nodes {
        ... on News {
          __typename
          id
          tag {
            id
            name
          }
          summaryShort
          title
          changedDate
          displayChangedDate
          publicationDate
          metaDescription
          path
          image {
            ... on Image {
              name
              src
            }
          }
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
        }
        ... on Blog {
          __typename
          id
          tag {
            id
            name
          }
          summaryShort
          title
          changedDate
          displayChangedDate
          metaDescription
          path
          image {
            ... on Image {
              name
              src
            }
          }
        blogEntries {
        ... on ParagraphBlogEntry {
          id
          title
          content {
            ... on ParagraphTextAndImage {
              id
              text
              style
              position
              image_style
              image_caption
              image {
                ... on MediaInterface {
                  ... on Image {
                    id
                    name
                    src
                    width
                    height
                    alt
                    description
                  }
                }
              }
            }
          }
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
