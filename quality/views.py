from django.shortcuts import render

# Vue pour la page d'accueil
def quality(request):
    return render(request, 'quality/quality.html')

def quality_detail_view(request):
    return render(request, 'quality/quality_detail.html')
