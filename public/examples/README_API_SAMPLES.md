# Public REST API Samples

Real-world API integration examples using free, public REST APIs.

## Sample Pipelines

### 1. JSONPlaceholder Users
**File**: `api-integration/jsonplaceholder_users_pipeline.json`  
**API**: https://jsonplaceholder.typicode.com/  
**Purpose**: Fetch user data by ID  
**Endpoints**: `/users/{id}`

### 2. Random User Generator
**File**: `api-integration/random_user_pipeline.json`  
**API**: https://randomuser.me/api/  
**Purpose**: Generate random user profiles  
**Endpoints**: `/?results={count}`

### 3. REST Countries
**File**: `api-integration/restcountries_pipeline.json`  
**API**: https://restcountries.com/  
**Purpose**: Query country information  
**Endpoints**: `/v3.1/alpha/{code}`

### 4. CoinGecko Crypto Prices
**File**: `api-integration/coingecko_pipeline.json`  
**API**: https://api.coingecko.com/  
**Purpose**: Get cryptocurrency prices  
**Endpoints**: `/api/v3/simple/price`

### 5. IP Geolocation
**File**: `api-integration/ip_geolocation_pipeline.json`  
**API**: https://ipapi.co/  
**Purpose**: Get location data for IP addresses  
**Endpoints**: `/{ip}`

### 6. Cat Facts
**File**: `api-integration/cat_facts_pipeline.json`  
**API**: https://catfact.ninja/  
**Purpose**: Fetch random cat facts  
**Endpoints**: `/fact`

### 7. GitHub Public API
**File**: `api-integration/github_public_pipeline.json`  
**API**: https://api.github.com/  
**Purpose**: Query public GitHub data  
**Endpoints**: `/users/{username}`, `/users/{username}/repos`

### 8. PokeAPI Pokemon Data
**File**: `api-integration/pokeapi_pipeline.json`  
**API**: https://pokeapi.co/  
**Purpose**: Query Pokemon data  
**Endpoints**: `/api/v2/pokemon/{id}`

## Common Patterns

### URL Construction
```sql
SELECT 
  id,
  'https://api.example.com/endpoint/' || id as api_url
FROM {{input}}
```

### Dynamic Parameters
```sql
SELECT 
  country,
  'https://api.example.com/data?country=' || country || '&format=json' as api_url
FROM {{input}}
```

### Multiple Endpoints
```sql
SELECT 
  item_id,
  'https://api.example.com/items/' || item_id as detail_url,
  'https://api.example.com/items/' || item_id || '/reviews' as reviews_url
FROM {{input}}
```

## Rate Limits

| API | Free Tier Limit | Notes |
|-----|----------------|-------|
| JSONPlaceholder | None | Pure testing API |
| RandomUser | None stated | Be reasonable |
| REST Countries | None stated | Be reasonable |
| CoinGecko | 10-50/min | Free tier |
| IP API | 1000/day | Free tier |
| Cat Facts | None stated | Be reasonable |
| GitHub | 60/hour | Unauthenticated |
| PokeAPI | None stated | Be reasonable |

## Best Practices

1. **Add delays between requests** when processing large batches
2. **Cache responses** when data doesn't change frequently
3. **Handle errors gracefully** - APIs may be temporarily unavailable
4. **Check rate limits** before making multiple requests
5. **Use appropriate HTTP methods** (GET for data retrieval)
6. **Validate responses** - check status codes and data structure

## Testing Tips

- Start with small batches (1-5 items)
- Verify API URLs in browser first
- Check API documentation for latest endpoints
- Monitor response times and errors
- Test error handling with invalid inputs

## Documentation Links

- JSONPlaceholder: https://jsonplaceholder.typicode.com/guide.html
- RandomUser: https://randomuser.me/documentation
- REST Countries: https://restcountries.com/#rest-countries
- CoinGecko: https://www.coingecko.com/en/api/documentation
- IP API: https://ipapi.co/json/
- Cat Facts: https://catfact.ninja/fact
- GitHub: https://docs.github.com/en/rest
- PokeAPI: https://pokeapi.co/docs/v2.html
