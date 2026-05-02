FROM nginx:alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy your shell files
COPY . /usr/share/nginx/html

# Expose port (nginx default)
EXPOSE 80