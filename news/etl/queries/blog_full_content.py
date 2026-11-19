QUERY = """
query BlogContentQuery($nodeID: Int!) {
  nodeByID(id: $nodeID){
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
              alt
              description
            }
          }
          blogEntries {
            ... on ParagraphBlogEntry {
              id
              title
              dateTime
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
}
"""
