## basic.jsonl

### 1
What are the main differences between renewable and non-renewable energy sources?

### 2
Write a short story about a robot discovering emotions for the first time.

### 3
List 5 practical tips for improving productivity while working from home.

### 4
How do you calculate the area of a circle? Show me the formula and an example.

### 5
Translate this sentence to French: 'The weather is beautiful today and I want to go for a walk.'

## structured-output.jsonl

### 1
The temperature in Tokyo is 90 degrees Fahrenheit.
```json
{
  "type": "OBJECT",
  "properties": {
    "locations_and_temperatures": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "location": {
            "type": "STRING"
          },
          "temperature": {
            "type": "NUMBER",
            "description": "Temperature in Celsius"
          }
        },
        "required": ["location", "temperature"],
        "propertyOrdering": ["location", "temperature"]
      }
    }
  },
  "required": ["locations_and_temperatures"]
}
```

### 2
John is 25 years old and works as a software engineer in New York. Sarah is 30 years old and is a data scientist in San Francisco.
```json
{
  "type": "OBJECT",
  "properties": {
    "people": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "name": { "type": "STRING" },
          "age": { "type": "NUMBER" },
          "job": { "type": "STRING" },
          "city": { "type": "STRING" }
        },
        "required": ["name", "age", "job", "city"],
        "propertyOrdering": ["name", "age", "job", "city"]
      }
    }
  },
  "required": ["people"]
}
```

### 3
The movie 'Inception' was released in 2010, directed by Christopher Nolan, and has a rating of 8.8/10. 'The Matrix' was released in 1999, directed by the Wachowskis, and has a rating of 8.7/10.
```json
{
  "type": "OBJECT",
  "properties": {
    "movies": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "title": {"type": "STRING"},
          "release_year": {"type": "NUMBER"},
          "director": {"type": "STRING"},
          "rating": {"type": "NUMBER"}
        },
        "required": ["title", "release_year", "director", "rating"],
        "propertyOrdering": ["title", "release_year", "director", "rating"]
      }
    }
  },
  "required": ["movies"]
}
```

### 4
The company Apple reported revenue of $394.3 billion in 2022. Microsoft reported revenue of $198.3 billion in the same year.
```json
{
  "type": "OBJECT",
  "properties": {
    "company_revenues": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "company": {
            "type": "STRING"
          },
          "revenue": {
            "type": "NUMBER",
            "description": "Revenue in billions USD"
          },
          "year": {
            "type": "NUMBER"
          }
        },
        "required": ["company", "revenue", "year"],
        "propertyOrdering": ["company", "revenue", "year"]
      }
    }
  },
  "required": ["company_revenues"]
}
```

### 5
The book '1984' by George Orwell has 328 pages and was published in 1949. 'To Kill a Mockingbird' by Harper Lee has 281 pages and was published in 1960.
```json
{
  "type": "OBJECT",
  "properties": {
    "books": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "title": {"type": "STRING"},
          "author": {"type": "STRING"},
          "pages": {"type": "NUMBER"},
          "publication_year": {"type": "NUMBER"}
        },
        "required": ["title", "author", "pages", "publication_year"],
        "propertyOrdering": ["title", "author", "pages", "publication_year"]
      }
    }
  },
  "required": ["books"]
}
```
