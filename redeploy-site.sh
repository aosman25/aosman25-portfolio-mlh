#!/bin/bash
cd aosman25-portfolio-mlh && 
git fetch && git reset origin/main --hard > /dev/null && 
docker compose -f docker-compose.prod.yml down && 
docker compose -f docker-compose.prod.yml up -d --build