# RUN THIS FIRST
# sed -n "s/version = \"\(.*\)\"/\1/p" pyproject.toml
# docker bake --build-arg VERSION=$VERSION -f docker-bake.hcl

target "default" {
    context = "."
    dockerfile = "Dockerfile"
    tags = [
        "ericklinares/gee-nieve-sequia-auto:$(VERSION)",
        "ericklinares/snow-ipa:$(VERSION)"
    ]
}