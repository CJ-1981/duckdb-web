# Public API Integration Samples - Complete Guide

## Overview
Comprehensive samples demonstrating real-world API integration with 8 different free public APIs. Each pipeline shows practical data fetching patterns.

## API Samples Summary

| API | Pipeline | Use Case | Endpoints |
|-----|----------|----------|-----------|
| JSONPlaceholder | jsonplaceholder_full_pipeline.json | Complete user data | /users/{id}, /posts, /albums |
| RandomUser | random_user_profiles_pipeline.json | User profile generation | /api/?results={n} |
| REST Countries | restcountries_regions_pipeline.json | Regional analysis | /v3.1/region/{region} |
| CoinGecko | coingecko_portfolio_pipeline.json | Crypto portfolio tracker | /api/v3/simple/price |
| IP API | ip_geolocation_batch_pipeline.json | Batch geolocation | /{ip}, /json/ |
| Cat Facts | cat_facts_collection_pipeline.json | Fact collection | /fact?max_length={n} |
| GitHub | github_repositories_pipeline.json | Repository analysis | /users/{username}/repos |
| PokeAPI | pokeapi_pokemon_evolution_pipeline.json | Pokemon evolution chains | /api/v2/pokemon/{id} |

## Usage Examples

### 1. JSONPlaceholder - Complete User Data
```
Input: User IDs (1-10)
Output: User URLs + posts + albums + todos + comments
Features: Multi-endpoint URLs, field extraction
```

### 2. RandomUser - Profile Generation
```
Input: Count, gender, nationality
Output: API URL with parameters
Features: Dynamic URL construction, field selection
```

### 3. REST Countries - Regional Analysis
```
Input: Region, fields to fetch
Output: Regional data + country-level fallback
Features: Field filtering, multiple endpoints
```

### 4. CoinGecko - Portfolio Tracker
```
Input: Crypto holdings + purchase prices
Output: Price URLs + cost basis calculation
Features: Portfolio value tracking, rate limit notes
```

### 5. IP API - Batch Processing
```
Input: IP addresses + types
Output: Geolocation URLs + field extraction
Features: Batch processing, fallback URLs, data fields
```

### 6. Cat Facts - Collection Builder
```
Input: Request ID, max length, category
Output: Fact URLs + alternative APIs
Features: Dynamic parameters, API alternatives
```

### 7. GitHub - Repository Analysis
```
Input: GitHub usernames + repo types
Output: User info + repos URLs + rate limits
Features: User vs org handling, rate limit awareness
```

### 8. PokeAPI - Evolution Chains
```
Input: Pokemon IDs + names + evolution flags
Output: Pokemon URLs + species URLs + evolution chains
Features: Multi-endpoint data, evolution chain URLs
```

## Common Patterns Demonstrated

### 1. Dynamic URL Construction
```sql
SELECT 
  id,
  'https://api.example.com/endpoint/' || id as api_url
FROM {{input}}
```

### 2. Multiple Endpoints
```sql
SELECT 
  id,
  'https://api.example.com/items/' || id as detail_url,
  'https://api.example.com/items/' || id || '/reviews' as reviews_url
FROM {{input}}
```

### 3. Query Parameters
```sql
SELECT 
  symbol,
  'https://api.example.com/price?symbol=' || symbol || '&currency=usd' as api_url
FROM {{input}}
```

### 4. Field Filtering
```sql
SELECT 
  region,
  'https://api.example.com/data?fields=' || fields as filtered_url
FROM {{input}}
```

### 5. Fallback URLs
```sql
SELECT 
  primary_url,
  primary_url || '/json' as fallback_url,
  'https://backup.example.com/' as emergency_fallback
FROM {{input}}
```

## Rate Limits Reference

| API | Free Limit | Paid Limit | Notes |
|-----|-----------|------------|-------|
| JSONPlaceholder | None stated | None | Testing API |
| RandomUser | None stated | None | Be reasonable |
| REST Countries | None stated | None | Be reasonable |
| CoinGecko | 10-50/min | Higher | Free tier |
| IP API | 1000/day | 100K/day | Free tier |
| Cat Facts | None stated | None | Be reasonable |
| GitHub | 60/hour | 5000/hour | Unauthenticated |
| PokeAPI | None stated | None | Be reasonable |

## Best Practices

### 1. Start Small
- Test with 1-5 items before scaling
- Verify API responses in browser first
- Check rate limits before batch processing

### 2. Handle Errors
- Always include fallback URLs
- Validate response structure
- Add timeout values

### 3. Rate Limiting
- Add delays between requests
- Cache responses when possible
- Use appropriate batch sizes

### 4. Documentation
- Include API documentation links
- Add rate limit notes
- Provide example responses

### 5. Field Selection
- Request only needed fields
- Use field filtering when available
- Reduce payload sizes

## Testing Checklist

- [ ] API URL accessible in browser
- [ ] Response format matches expectations
- [ ] Rate limits checked
- [ ] Error handling tested
- [ ] Multiple items processed successfully
- [ ] Output data validates correctly

## File Structure

```
public/examples/
├── api-integration/
│   ├── jsonplaceholder_full_pipeline.json
│   ├── random_user_profiles_pipeline.json
│   ├── restcountries_regions_pipeline.json
│   ├── coingecko_portfolio_pipeline.json
│   ├── ip_geolocation_batch_pipeline.json
│   ├── cat_facts_collection_pipeline.json
│   ├── github_repositories_pipeline.json
│   └── pokeapi_pokemon_evolution_pipeline.json
└── examples/
    ├── jsonplaceholder_users.csv
    ├── user_profile_requirements.csv
    ├── regions_list.csv
    ├── crypto_portfolio.csv
    ├── ip_batch.csv
    ├── cat_fact_requests.csv
    ├── github_repositories.csv
    └── pokemon_query.csv
```

## Real-World Use Cases

### E-commerce
- **RandomUser**: Generate test customer profiles
- **REST Countries**: Validate addresses and shipping
- **CoinGecko**: Process cryptocurrency payments

### Data Analysis
- **GitHub**: Analyze repository trends
- **IP API**: Fraud detection and location analytics
- **Cat Facts**: Content generation for blogs

### Testing
- **JSONPlaceholder**: API integration testing
- **PokeAPI**: Game data testing
- **REST Countries**: Internationalization testing

### Development
- **All APIs**: Prototyping and mock data generation
- **GitHub**: CI/CD integration testing
- **RandomUser**: User interface testing

## Quick Start

1. Choose an API pipeline from the Samples tab
2. Load the pipeline into the workflow editor
3. Review the API URLs being constructed
4. Execute the pipeline
5. Export or process the results

All pipelines are production-ready and use real, working public APIs!
