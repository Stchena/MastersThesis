from spacy.language import Language
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from sklearn.cluster import KMeans
import numpy as np


def read_file_content(filepath: str):
    with open(filepath, 'r') as f:
        content = [line.rstrip('\n') for line in f]
        return content


@Language.component('money_merger')
def money_merger(doc):
    with doc.retokenize() as retokenizer:
        for money in [e for e in doc.ents if e.label_ == 'MONEY']:
            if doc[money.start - 1].is_currency:
                retokenizer.merge(doc[
                    money.start-1:money.end])
    return doc


def print_topics(method, feature_names, n_top_words=15):
    for i, topic_vec in enumerate(method.components_):
        print(i, end=' ')
        # topic_vec.argsort() produces a new array
        # in which word_index with the least score is the
        # first array element and word_index with highest
        # score is the last array element. Then using a
        # fancy indexing [-1: -n_top_words-1:-1], we are
        # slicing the array from its end in such a way that
        # top `n_top_words` word_index with highest scores
        # are returned in desceding order
        for fid in topic_vec.argsort()[-1:-n_top_words-1:-1]:
            print(feature_names[fid], end=', ')
        print()
    return 0


def generate_wordclouds(X, in_X_tfidf, k, in_word_positions, file_prefix):
    # Clustering
    in_model = KMeans(n_clusters=k, random_state=289925, n_jobs=-1)
    in_y_pred = in_model.fit_predict(X)
    in_cluster_ids = set(in_y_pred)
    silhouette_avg = silhouette_score(X, in_y_pred)
    print("For n_clusters =", k, "The average silhouette_score is :", silhouette_avg)

    # Number of words with highest tfidf score to display
    top_count = 100

    for in_cluster_id in in_cluster_ids:
        # compute the total tfidf for each term in the cluster
        in_tfidf = in_X_tfidf[in_y_pred == in_cluster_id]
        # numpy.matrix
        tfidf_sum = np.sum(in_tfidf, axis=0)
        # numpy.array of shape (1, X.shape[1])
        tfidf_sum = np.asarray(tfidf_sum).reshape(-1)
        top_indices = tfidf_sum.argsort()[-top_count:]
        term_weights = {in_word_positions[in_idx]: tfidf_sum[in_idx] for in_idx in top_indices}
        wc = WordCloud(width=1200, height=800, background_color="white")
        wordcloud = wc.generate_from_frequencies(term_weights)
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        fig.suptitle(f"Cluster {in_cluster_id}")
        plt.savefig(f"{file_prefix}_cluster_{in_cluster_id}.png")
        plt.show()

    return in_cluster_ids

def plot_top_words(model, feature_names, n_top_words, title):
    fig, axes = plt.subplots(2, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f'Topic {topic_idx +1}',
                     fontdict={'fontsize': 30})
        ax.invert_yaxis()
        ax.tick_params(axis='both', which='major', labelsize=20)
        for i in 'top right left'.split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    plt.show()
    return 0

def get_recommendation(source_article_id, articles, model, similarity_measure=cosine_similarity, text_repr=None):
    similarities = similarity_measure(model)
    # get recommends for one specific article
    similar_articles = list(enumerate(similarities[source_article_id]))
    # Sort the similarities in order of closest similarity
    similar_articles = sorted(similar_articles, key=lambda x: x[1], reverse=True)
    # Return tuple of the requested closest scores excluding the target item and index
    similar_articles = similar_articles[1:6] # limit=5
    similar_articles_ids, similar_articles_score = list(zip(*similar_articles))
    recommended_articles_titles = [articles[idx].title for idx in similar_articles_ids]
    print(f"=={text_repr}==")
    print(f"Source article:\n{articles[source_article_id]}")
    print("Recommended articles:")
    for i, (title, score) in enumerate(zip(recommended_articles_titles, similar_articles_score)):
        print(i, title, "{:.1%}".format(score), sep=' ')