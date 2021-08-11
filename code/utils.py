from spacy.language import Language
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel


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


def plot_top_words(model, subplots_x, subplots_y, feature_names, n_top_words, title):
    fig, axes = plt.subplots(subplots_x, subplots_y, figsize=(30, 15), sharex=True)
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

def get_recommendation(source_article_id, articles, model, similarity_measure=cosine_similarity, text_repr=None):
    similarities = similarity_measure(model)
    # get recommends for one specific article
    similar_articles = list(enumerate(similarities[source_article_id]))
    # Sort the similarities in order of closest similarity
    similar_articles = sorted(similar_articles, key=lambda x: x[1], reverse=True)
    # Return tuple of the requested closest scores excluding the target item and index
    similar_articles = [x for x in similar_articles if x[0] != source_article_id][0:5]
    similar_articles_ids, similar_articles_score = list(zip(*similar_articles))
    recommended_articles_titles = [articles[idx].title for idx in similar_articles_ids]
    print(f"=={text_repr}==")
    print(f"Source article:\n{articles[source_article_id]}")
    print("Recommended articles:")
    for i, (title, score) in enumerate(zip(recommended_articles_titles, similar_articles_score)):
        print(i+1, f"|| ArticleID:{similar_articles_ids[i]} ||")
        print(title, "|| Similarity: {:.1%} ||".format(score), sep=' ')